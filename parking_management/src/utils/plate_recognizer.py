import onnxruntime as ort
from src.utils.logger import get_logger
import cv2
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
import copy

class PlateRecognizer:
    def __init__(self, detect_model_path, rec_model_path,
                 detect_conf_thresh: float = None,
                 iou_thresh: float = None,
                 input_size=(640, 640),
                 use_clahe: bool = False,
                 ort_providers: list = None,
                 ort_intra_threads: int = None):
        """
        PlateRecognizer 支持一些运行时优化参数（均为可选，向后兼容）：
        - detect_conf_thresh: 检测置信度阈值（默认 0.3 或来自环境）
        - iou_thresh: NMS IOU 阈值（默认 0.5 或来自环境）
        - input_size: 检测模型输入大小（默认 (640,640)）
        - use_clahe: 在识别前是否对车牌图像使用 CLAHE 增强
        - ort_providers: 优先使用的 ONNX Runtime providers 列表（例如 ['CUDAExecutionProvider']）
        - ort_intra_threads: 设置 ORT session 的 intra_op_num_threads
        """
        # 可从环境变量读取覆盖（如果未通过参数显式提供）
        try:
            env_conf = float(os.environ.get('PLATE_DET_CONF_THRESH')) if os.environ.get('PLATE_DET_CONF_THRESH') else None
        except Exception:
            env_conf = None
        try:
            env_iou = float(os.environ.get('PLATE_DET_IOU_THRESH')) if os.environ.get('PLATE_DET_IOU_THRESH') else None
        except Exception:
            env_iou = None

        self.conf_thresh = detect_conf_thresh if detect_conf_thresh is not None else (env_conf if env_conf is not None else 0.3)
        self.iou_thresh = iou_thresh if iou_thresh is not None else (env_iou if env_iou is not None else 0.5)
        self.input_size = tuple(input_size)
        self.use_clahe = use_clahe or os.environ.get('PLATE_USE_CLAHE', '0') in ('1', 'true', 'True')

        # ONNX Runtime session options（线程与 providers）
        self.ort_providers = ort_providers or (['CUDAExecutionProvider'] if os.environ.get('PLATE_USE_CUDA') in ('1', 'true', 'True') else ['CPUExecutionProvider'])
        try:
            env_threads = int(os.environ.get('ORT_INTRA_THREADS')) if os.environ.get('ORT_INTRA_THREADS') else None
        except Exception:
            env_threads = None
        self.ort_intra_threads = ort_intra_threads if ort_intra_threads is not None else (env_threads if env_threads is not None else 1)

        # 初始化 logger 以便记录后续 provider 尝试信息
        self.logger = get_logger('PlateRecognizer')

        # 创建 session options（尽量对 CPU 多线程与内存使用进行配置）
        so = None
        try:
            # 有些 onnxruntime 发行版（或错误安装/命名冲突）可能没有 SessionOptions
            if hasattr(ort, 'SessionOptions'):
                so = ort.SessionOptions()
                try:
                    so.intra_op_num_threads = int(self.ort_intra_threads)
                except Exception:
                    pass
            else:
                self.logger.warning('onnxruntime 模块缺少 SessionOptions，继续但不会为 InferenceSession 提供 sess_options')
        except Exception as e:
            # 记录但继续尝试创建 session（不传 sess_options）
            try:
                self.logger.exception(f'创建 SessionOptions 时出错: {e}')
            except Exception:
                pass
            so = None

        def _try_create_session(model_path, providers_list):
            """尝试按 providers_list 的优先顺序创建 InferenceSession，记录失败信息并回退到 CPU。"""
            last_exc = None
            for prov in providers_list:
                try:
                    # providers expects a list in ort.InferenceSession
                    self.logger.info(f"尝试使用 ONNX Runtime provider: {prov} 加载 {model_path}")
                    # 仅当 so 可用时传入 sess_options（有些 ort 构建可能不支持此参数）
                    if so is not None:
                        sess = ort.InferenceSession(model_path, sess_options=so, providers=[prov])
                    else:
                        sess = ort.InferenceSession(model_path, providers=[prov])
                    self.logger.info(f"使用 provider {prov} 成功加载 {model_path}")
                    return sess, prov
                except Exception as e:
                    last_exc = e
                    try:
                        self.logger.warning(f"provider {prov} 无法加载模型 {model_path}: {e}")
                    except Exception:
                        pass
            # 最后尝试 CPU
            try:
                self.logger.info(f"尝试回退到 CPUExecutionProvider 加载 {model_path}")
                if so is not None:
                    sess = ort.InferenceSession(model_path, sess_options=so, providers=['CPUExecutionProvider'])
                else:
                    sess = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
                self.logger.info(f"使用 provider CPUExecutionProvider 成功加载 {model_path}")
                return sess, 'CPUExecutionProvider'
            except Exception as e:
                try:
                    self.logger.exception(f"所有 provider 尝试失败，加载模型 {model_path} 失败")
                except Exception:
                    pass
                # 最终抛出以便上层了解初始化失败
                raise last_exc or e

        # 加载 ONNX 模型（按优先 provider 列表尝试，失败回退到 CPU）
        try:
            self.detect_session, used_detect_provider = _try_create_session(detect_model_path, self.ort_providers)
            self.detect_provider = used_detect_provider
            self.logger.info(f"检测模型使用的 provider: {used_detect_provider}")
        except Exception:
            # 让初始化失败被上层捕获（更显式）
            raise

        try:
            self.rec_session, used_rec_provider = _try_create_session(rec_model_path, self.ort_providers)
            self.rec_provider = used_rec_provider
            self.logger.info(f"识别模型使用的 provider: {used_rec_provider}")
        except Exception:
            raise

        self.camera = None
        self.plate_color_list = ['黑色', '蓝色', '绿色', '白色', '黄色']
        self.plateName = r"#京沪津渝冀晋蒙辽吉黑苏浙皖闽赣鲁豫鄂湘粤桂琼川贵云藏陕甘青宁新学警港澳挂使领民航危0123456789ABCDEFGHJKLMNPQRSTUVWXYZ险品"
        self.mean_value, self.std_value = (0.588, 0.193)  # 识别模型均值标准差（可后续从 config 注入）

    def preprocess_image(self, image):
        # 检测前处理
        img, r, left, top = self.my_letter_box(image, self.input_size)
        img = img[:, :, ::-1].transpose(2, 0, 1).copy().astype(np.float32)
        img = img / 255
        img = img.reshape(1, *img.shape)
        return img, r, left, top

    def my_letter_box(self, img, size=(640, 640)):
        h, w, c = img.shape
        r = min(size[0] / h, size[1] / w)
        new_h, new_w = int(h * r), int(w * r)
        top = int((size[0] - new_h) / 2)
        left = int((size[1] - new_w) / 2)
        bottom = size[0] - new_h - top
        right = size[1] - new_w - left
        img_resize = cv2.resize(img, (new_w, new_h))
        img = cv2.copyMakeBorder(img_resize, top, bottom, left, right, borderType=cv2.BORDER_CONSTANT, value=(114, 114, 114))
        return img, r, left, top

    def detect_plate(self, image):
        # 使用检测模型找到车牌
        img, r, left, top = self.preprocess_image(image)
        # 尝试使用 IO binding（当使用 CUDAExecutionProvider 且当前 ort 版本支持时），以减少 host<->device 复制
        y_onnx = None
        try:
            providers = getattr(self.detect_session, 'get_providers', lambda: [])()
        except Exception:
            providers = []

        try:
            if any('CUDA' in p for p in providers) and hasattr(self.detect_session, 'io_binding'):
                try:
                    io_binding = self.detect_session.io_binding()
                    # bind CPU numpy input; ONNX Runtime 会在需要时将其复制到 CUDA
                    io_binding.bind_cpu_input(self.detect_session.get_inputs()[0].name, img)
                    io_binding.bind_output(self.detect_session.get_outputs()[0].name)
                    self.detect_session.run_with_iobinding(io_binding)
                    outputs = io_binding.copy_outputs_to_cpu()[0]
                    y_onnx = outputs
                except Exception:
                    y_onnx = None
        except Exception:
            y_onnx = None

        if y_onnx is None:
            y_onnx = self.detect_session.run([self.detect_session.get_outputs()[0].name], {self.detect_session.get_inputs()[0].name: img})[0]
        outputs = self.post_processing(y_onnx, r, left, top)
        return outputs

    def post_processing(self, dets, r, left, top, conf_thresh=None, iou_thresh=None):
        # 使用实例阈值（优先函数参数，其次实例配置）
        conf = conf_thresh if conf_thresh is not None else self.conf_thresh
        iou = iou_thresh if iou_thresh is not None else self.iou_thresh
        choice = dets[:, :, 4] > conf
        dets = dets[choice]
        dets[:, 13:15] *= dets[:, 4:5]
        box = dets[:, :4]
        boxes = self.xywh2xyxy(box)
        score = np.max(dets[:, 13:15], axis=-1, keepdims=True)
        index = np.argmax(dets[:, 13:15], axis=-1).reshape(-1, 1)
        output = np.concatenate((boxes, score, dets[:, 5:13], index), axis=1)
        reserve_ = self.my_nms(output, iou)
        output = output[reserve_]
        output = self.restore_box(output, r, left, top)
        return output

    def xywh2xyxy(self, boxes):
        xywh = copy.deepcopy(boxes)
        xywh[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
        xywh[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
        xywh[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
        xywh[:, 3] = boxes[:, 1] + boxes[:, 3] / 2
        return xywh

    def my_nms(self, boxes, iou_thresh):
        # boxes 格式假定为 [x1,y1,x2,y2,score, ...]
        index = np.argsort(boxes[:, 4])[::-1]
        keep = []
        while index.size > 0:
            i = index[0]
            keep.append(i)
            x1 = np.maximum(boxes[i, 0], boxes[index[1:], 0])
            y1 = np.maximum(boxes[i, 1], boxes[index[1:], 1])
            x2 = np.minimum(boxes[i, 2], boxes[index[1:], 2])
            y2 = np.minimum(boxes[i, 3], boxes[index[1:], 3])
            w = np.maximum(0, x2 - x1)
            h = np.maximum(0, y2 - y1)
            inter_area = w * h
            union_area = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1]) + (boxes[index[1:], 2] - boxes[index[1:], 0]) * (boxes[index[1:], 3] - boxes[index[1:], 1])
            iou = inter_area / (union_area - inter_area)
            idx = np.where(iou <= iou_thresh)[0]
            index = index[idx + 1]
        return keep

    def restore_box(self, boxes, r, left, top):
        boxes[:, [0, 2, 5, 7, 9, 11]] -= left
        boxes[:, [1, 3, 6, 8, 10, 12]] -= top
        boxes[:, [0, 2, 5, 7, 9, 11]] /= r
        boxes[:, [1, 3, 6, 8, 10, 12]] /= r
        return boxes

    def recognize_text(self, plate_image):
        # 使用识别模型提取车牌文字
        img = self.rec_pre_processing(plate_image)
        # 尝试使用 IO binding（当使用 CUDAExecutionProvider 且当前 ort 版本支持时）
        y_onnx_plate = None
        y_onnx_color = None
        try:
            providers = getattr(self.rec_session, 'get_providers', lambda: [])()
        except Exception:
            providers = []

        try:
            if any('CUDA' in p for p in providers) and hasattr(self.rec_session, 'io_binding'):
                try:
                    io_binding = self.rec_session.io_binding()
                    io_binding.bind_cpu_input(self.rec_session.get_inputs()[0].name, img)
                    io_binding.bind_output(self.rec_session.get_outputs()[0].name)
                    io_binding.bind_output(self.rec_session.get_outputs()[1].name)
                    self.rec_session.run_with_iobinding(io_binding)
                    outs = io_binding.copy_outputs_to_cpu()
                    y_onnx_plate, y_onnx_color = outs[0], outs[1]
                except Exception:
                    y_onnx_plate = None
                    y_onnx_color = None
        except Exception:
            y_onnx_plate = None
            y_onnx_color = None

        if y_onnx_plate is None or y_onnx_color is None:
            y_onnx_plate, y_onnx_color = self.rec_session.run([self.rec_session.get_outputs()[0].name, self.rec_session.get_outputs()[1].name], {self.rec_session.get_inputs()[0].name: img})
        index = np.argmax(y_onnx_plate, axis=-1)
        index_color = np.argmax(y_onnx_color)
        plate_color = self.plate_color_list[index_color]
        plate_no = self.decode_plate(index[0])
        return plate_no, plate_color

    def rec_pre_processing(self, img, size=(48, 168)):
        # 识别前处理，支持可选 CLAHE 增强
        target_w, target_h = size[1], size[0]
        img = cv2.resize(img, (target_w, target_h))
        if self.use_clahe:
            try:
                lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                cl = clahe.apply(l)
                merged = cv2.merge((cl, a, b))
                img = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
            except Exception:
                pass
        img = img.astype(np.float32)
        img = (img / 255 - self.mean_value) / self.std_value
        img = img.transpose(2, 0, 1)
        img = img.reshape(1, *img.shape)
        return img

    def decode_plate(self, preds):
        pre = 0
        new_preds = []
        for i in range(len(preds)):
            if preds[i] != 0 and preds[i] != pre:
                new_preds.append(preds[i])
            pre = preds[i]
        plate = ""
        for i in new_preds:
            plate += self.plateName[int(i)]
        return plate

    def capture_and_recognize(self):
        # 使用摄像头捕获图像并识别车牌
        if self.camera is None:
            self.camera = cv2.VideoCapture(0)

        ret, frame = self.camera.read()
        if not ret:
            return False, "无法从摄像头读取图像"

        outputs = self.detect_plate(frame)
        if outputs is not None:
            for output in outputs:
                rect = output[:4].astype(int)
                plate_image = frame[rect[1]:rect[3], rect[0]:rect[2]]
                plate_no, plate_color = self.recognize_text(plate_image)
                return True, f"车牌号: {plate_no}, 颜色: {plate_color}"

        return False, "未检测到车牌"

    def stop_camera(self):
        # 停止摄像头
        if self.camera is not None:
            self.camera.release()
            self.camera = None
