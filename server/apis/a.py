

import os
import time
print(os.getcwd())

random_dir = time.strftime("%Y%m%d_%H%M%S")[2:]


os.makedirs("../../uploads/"+random_dir+"/",exist_ok=True)
with open("../../uploads/"+random_dir+"/test","wb") as f:
    f.write(b"1")


