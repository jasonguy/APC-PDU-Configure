"""
Exmaple client using the apc module
"""

from apc import ApcPdu

pdu = ApcPdu('192.168.1.1, 'apc', 'apc)

# Open connection
pdu.connect()

# Download config to the local machine
pdu.getConfig()

# Parse the config into an array
pduConfig = pdu.parseConfig()

# Now the fun part, change values.  Refer to an existing config.ini
# for exactly what to change.  A few basics are here for reference, but
# the syntax is config[directive][item] = value, where directive is
# something like [NetworkTCP/IP] that's in a regular config.ini, item
# is what goes on the left side of the config line, value is the right side.
#
# Setting something here will overwrite an existing value, be careful!
pduConfig['SystemID']['Contact'] = 'Testing'

# Write the config back to the system, exit if it doesn't work.  If notices
# are turned on, you'll get a message.
pdu.writeConfig(pduConfig)

# Close the connection
pdu.close()