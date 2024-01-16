<h1 align="center">Project NAM
<h3 align="center">Self hosted architecture for communication with Open AI</h3>
<p>You are currently viewing a <b>server</b>. You can use <b>server</b> to serve nam clients:
<p><b>* download client</b>  -  https://github.com/Ivashkka/nam_client
<p>
<p><b>install:</b>
<p>create directory for clonning git repo on your machine:
<p>cd ~
<p>mkdir nam_repos; cd nam_repos
<p>clone nam repo:
<p>git clone https://github.com/Ivashkka/nam.git
<p>cd nam
<p>start make install from root
<p>sudo make install
<p>wait until instalation finishes
<p>after installation is complete you can start nam_server:
<p>systemctl start nam_server
<p>systemctl status nam_server
<p>and enable if needed:
<p>systemctl enable nam_server
<p>
<p><b>settings:</b>
<p>all server settings located in /etc/nam_server
<p>conf.yaml - primary config file
<p>edit ip and port to listen in conf.yaml
<p>users.json - file to store users data
<p>
<p><b>usage:</b>
<p>to interact with server - use namctl instrument
<p>use namctl help to get info about any commands
<p>note: do not use namctl inside nam git repo directory(where you cloned nam.git), this can lead to bugs
<p>
<p><b>uninstall:</b>
<p>stop server:
<p>systemctl stop nam_server
<p>or use namctl stop
<p>disable autorun if needed:
<p>systemctl disable nam_server
<p>move inside nam git repo directory(where you cloned nam.git):
<p>cd ~/nam_repos/nam
<p>start uninstall process:
<p>make clean
<p>
<p>note: latest version is - v1.0.0unstable. There may be a few bugs
