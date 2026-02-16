Victron Solar Charger Modbus checks for CheckMK

Thes do not need any external libraries - just copy them into `/omd/sites/^YOUR SITE NAME^/local/lib/nagios/plugins`, make them executeable and then activate them as a Nagios active check - simplest way is to use `$USER2$/python_file.py $HOSTADDRESS$`
This way the python file will inherit the IP address of the host that the active check is assigned too. 



These python checks were written with the intention of being able to iterate through multiple modbus registers and present the data as multiple services from a single extension, I haven't got that part working yet, but that is why the for loop exists in the script. 
Extending the program to use that for loop is quite simple, just add registers to the "points" struct and the for loop will iterate through them
