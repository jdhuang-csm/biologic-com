# `biologic-com`: a Python package for programmable experiments with BioLogic potentiostats
`biologic-com` is a Python package that enables programmatic creation of `.mps` settings files and real-time control of BioLogic devices via the EC-Lab OLECOM interface. With `biologic-com`, you can:
* Create customized `.mps` settings files for a variety of experiments using Python scripts
* Use EC-Lab as a server to load, execute, and stop experiments via Python
* Asynchronously control/monitor multiple channels or devices

## Why OLECOM control?
The OLECOM interface allows you to execute experiments through EC-Lab, which ensures that the firmware and collected data are the same as when using the graphical user interface. It is also possible to interface directly with the instrument using the EC-Lab Development Package (see, for example, [easy-biologic](https://github.com/bicarlsen/easy-biologic)). However, this loads different firmware to the instrument, which in my experience results in a lower signal-to-noise ratio for certain experiments compared to the standard firmware.

## Installation and setup
To use `biologic-com` to control EC-Lab, you first need to register EC-Lab as an OLECOM server by following the procedure in Section 2 of the included OLECOM PDF manual.

## Documentation
Documentation and examples will be added soon.

