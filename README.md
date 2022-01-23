# Unifi Checkmk addon

This project contains an addon for Unifi devices (https://ui.com/).

The special agent supports all Unifi network components and creates dynamic hosts via piggiback data..

Don't hesitate to ask for additional check plugins.

# Bugs / Important stuff

- no bugs known at the moment.

# Building

To build all the plugins, clone [this repository]
and run:

    make all

(Make sure to have make and Python3 installed.)

You can also build a single plugin, e.g.:

    make 

The files (*.mkp) will be written into the `build/` directory.


# Installing

SSH into your Check_MK machine, change to the user of the site you want to install the plugin,
then run:

    mkp install /path/to/plugin.mkp

or use WATO to install.

then configure the scpecial agent for the unifi controller device.
If you enable dynamic creation of hosts for piggiback data, a host for every unifi device will be created.


# License
Apache 2
