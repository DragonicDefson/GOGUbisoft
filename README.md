# GOGUbisoft
Fixed Ubisoft Connect integration for the GOG Galaxy application

# Important notices (per request of @MisterOizo)
Make sure to have GOG closed while replacing the integration.

# Installation step 1 (Downloading the files, and extracting them)
Download the repository files, and extract the .zip compressed file to a folder that
resides on a for you accessible place.

# Installation step 2 (Creating the integration folder)
Open the GOG Galaxy application, and if you've not done it yet, install the original Ubisoft integration, this can be done by using
the search menu in the settings sub-menu.

This will generate the uplay_ integration folder, followed by a random uid.  
Example: uplay_afb5a69c-b2ee-4d58-b916-f4cd75d4999a

This folder can be found on a computer running a Windows operating system here:  
Example: C:\Users\your username\AppData\Local\GOG.com\Galaxy\plugins\installed\uplay_afb5a69c-b2ee-4d58-b916-f4cd75d4999a

# Installation step 3 (Replacing the files)
Head over to the path in the example above, remember, the uplay_ prefix is always the same, but the uid differs.  
Example: afb5a69c-b2ee-4d58-b916-f4cd75d4999a (this differs).

Delete all the  files inside the folder, head over to the downloaded files and copy them to the folder with the prefix.
Close the folder, restart the GOG Galaxy application, and authenticate through the integration with Ubisoft.
