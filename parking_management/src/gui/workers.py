from PySide6.QtCore import QThread, Signal
import cv2


class RecognizeWorker(QThread):
    """在后台线程进行图片检测与识别，完成后发出信号。"""
    finished = Signal(dict)

    def __init__(self, plate_recognizer, image_path, parent=None):
        super().__init__(parent)
        self.plate_recognizer = plate_recognizer
        self.image_path = image_path

    def run(self):
        result = {'ok': False, 'msg': '未检测到车牌', 'plate': None, 'color': None}
        try:
            img = cv2.imread(self.image_path)
            if img is None:
                result['msg'] = '无法读取图片文件'
                self.finished.emit(result)
                return
            outputs = None
            try:
                outputs = self.plate_recognizer.detect_plate(img)
            except Exception:
                result['msg'] = 'detect_plate 调用失败'
                try:
                    # fallback: put exception info into msg? keep simple
                    pass
                except Exception:
                    pass
            if outputs is not None and len(outputs) > 0:
                rect = outputs[0][:4].astype(int)
                plate_image = img[rect[1]:rect[3], rect[0]:rect[2]]
                try:
                    plate_no, plate_color = self.plate_recognizer.recognize_text(plate_image)
                    result.update({'ok': True, 'msg': '识别成功', 'plate': plate_no, 'color': plate_color})
                except Exception:
                    result['msg'] = '识别车牌时出错'
            else:
                result['msg'] = '图片中未检测到车牌'
        except Exception:
            result['msg'] = '后台识别发生异常'
        self.finished.emit(result)
