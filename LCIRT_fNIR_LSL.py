
# TEST SCRIPT 
# NOT FINAL


import nidaqmx.system
import time
import pylsl

info = pylsl.stream_info('BioSemi', 'fnir', 1, 100, pylsl.cf_float32, 'myuid34234') #'float32'

# next make an outlet
outlet = None
outlet = pylsl.stream_outlet(info)
task = nidaqmx.Task()

for num in range(1,17):
    task.ai_channels.add_ai_voltage_chan('{0}{1}'.format('Dev1/ai',num-1))

   
print("now sending data...")
while True:
    datarec = task.read(number_of_samples_per_channel=1)
    #outlet.push_sample(data)
    stamp = time.time() #100 #local_clock()-0.125
    #values=[datarec[1], datarec[2]]
    outlet.push_sample(pylsl.vectord(datarec[1]), stamp)

