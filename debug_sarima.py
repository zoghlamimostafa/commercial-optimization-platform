import traceback
import sys

try:
    import sarima_delivery_optimization as sdo
except Exception as e:
    traceback.print_exc(file=sys.stdout)
