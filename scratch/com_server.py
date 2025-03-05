from biocom.com.server import OLECOM

ole = OLECOM()

ole.launch_server()

ole.toggle_popups(True)

ole.get_device_type(0)
ole.check_measure_status(1, 1)
ole.get_channel_info(1, 1)

ole.server.GetExperimentInfos(1, 1)
ole.connect_device(0)

ole.server.EnabledMessagesWindows()

stat = ole.check_measure_status(1, 1)

len(stat)