import sys
sys.path.append(r'd:\parking_lot_management\parking_management')

try:
    from src.utils.config import Config
    from src.core.parking_lot import ParkingLot
    c = Config()
    print('Config loaded, data_dir=', c.get_data_dir())
    p = ParkingLot()
    print('ParkingLot loaded, total_spaces=', p.total_spaces)
except Exception as e:
    print('ERROR', type(e), e)
    raise
