import asyncio
from collections import deque
import time
import numpy as np
import matplotlib.pyplot as plt


channel_duration = {
    'a': 1,
    'b': 2,
    'c': 3
}


# Basic
async def wait_for_channel(name, channel_status):
    start = time.monotonic()
    print(f'Channel {name} starting')
    while True:
        elapsed = time.monotonic()  - start
        if  elapsed >= channel_duration[name]:
            break
        await asyncio.sleep(0.5)
        
    print(f'Channel {name} done in {elapsed} s')
    channel_status[name] = True
    return elapsed

async def wait_for_channels(names, channel_status):
    return await asyncio.gather(*[wait_for_channel(name, channel_status) for name in names])


async def print_junk():
    for i in range(5):
        print(f"Junk {i}")
        await asyncio.sleep(0.5)
        
        
async def run_all(names):
    channel_status = {}
    return await asyncio.gather(*[wait_for_channel(name, channel_status) for name in names], print_junk())
    # return await asyncio.gather(wait_for_channels(names, channel_status), print_junk())



asyncio.run(run_all(list(channel_duration.keys())))
asyncio.run(wait_for_channels(list(channel_duration.keys()), {}))
asyncio.run(print_junk())



# async def wait_for_all():
#     await asyncio.gather(
#         *[wait_for_channel(k) for k in channel_duration.keys()]
#     )

# Better
# def check_channel(t_init, name):
#     elapsed = time.monotonic()  - t_init
#     return elapsed >= channel_duration[name]
    
async def log_temp(log, t_init, channel_status):
    while not all([channel_status.get(k, False) for k in channel_duration.keys()]):
        # print('temp log')
        elapsed = time.monotonic() - t_init
        temp = 25 + 25 * (1 - np.exp(-elapsed / 5))
        log.append([elapsed, temp])
        await asyncio.sleep(0.5)
    print('temp log done')
    

def temp_is_stable(log, sp=50):
    tt = np.array(log)[-10:]
    temps = tt[:, 1]
    slope = np.polyfit(tt[:, 0], tt[:, 1], deg=1)[0]
    abs_diffs = np.abs(temps - sp)
    return all([
        np.mean(abs_diffs) <= 0.5,
        np.max(abs_diffs) <= 1.0,
        slope <= 0.01,
    ])
        
    
    
async def wait_for_all_wlog(log, t_init):
    channel_status = {}
    return await asyncio.gather(
        *[wait_for_channel(k, channel_status) for k in channel_duration.keys()],
        log_temp(log, t_init, channel_status)
    )
        



temp_log = deque()
t0 = time.monotonic()
while True:
    result = asyncio.run(wait_for_all_wlog(temp_log, t0))
    if temp_is_stable(temp_log):
        break
    
for i in range(2):
    result = asyncio.run(wait_for_all_wlog(temp_log, t0))
    
temp_log



tt = np.array(temp_log)
fig, ax = plt.subplots()
ax.scatter(tt[:, 0], tt[:, 1])
plt.show()


tt[:, 0]