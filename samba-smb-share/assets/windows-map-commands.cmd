:: Show existing SMB mappings
net use

:: Delete all connections to this SMB server
net use \\192.168.31.70\* /delete

:: Map Data0_xuke to drive Z:
net use Z: \\192.168.31.70\Data0_xuke /user:xuke PASSWORD

:: Delete mapped drive Z:
net use Z: /delete
