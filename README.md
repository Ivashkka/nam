<h1 align="center">Project NAM
<h3 align="center">Self hosted architecture for communication with Open AI</h3>
<p>You are currently viewing a <b>server</b>. You can use <b>server</b> to serve nam clients:</p>
<p><b>* download client</b>  -  https://github.com/Ivashkka/nam_client</p>
<br>
<p><b>install:</b></p>
<p>install make package:</p>
<p><code>apt install make</code></p>
<p>create directory for clonning git repo on your machine:</p>
<p><code>cd ~</code></p>
<p><code>mkdir nam_repos; cd nam_repos</code></p>
<p>clone nam repo:</p>
<p><code>git clone https://github.com/Ivashkka/nam.git</code></p>
<p><code>cd nam</code></p>
<p>start make install from root:</p>
<p><code>sudo make install</code></p>
<p>wait until instalation finishes</p>
<p>after installation is complete you can start nam_server:</p>
<p><code>systemctl start nam_server</code></p>
<p><code>systemctl status nam_server</code></p>
<p>and enable if needed:</p>
<p><code>systemctl enable nam_server</code></p>
<br>
<p><b>settings:</b></p>
<p>all server settings located in /etc/nam_server</p>
<p>conf.yaml - primary config file</p>
<p>edit ip and port to listen in conf.yaml</p>
<p>users.json - file to store users data</p>
<br>
<p><b>usage:</b></p>
<p>to interact with server - use namctl instrument</p>
<p>use <code>namctl help</code> to get info about any commands</p>
<p>note: do not use namctl inside nam git repo directory(where you cloned nam.git), this can lead to bugs</p>
<br>
<p><b>uninstall:</b></p>
<p>stop server:</p>
<p><code>systemctl stop nam_server</code></p>
<p>or use <code>namctl stop</code></p>
<p>disable autorun if needed:</p>
<p><code>systemctl disable nam_server</code></p>
<p>move inside nam git repo directory(where you cloned nam.git):</p>
<p><code>cd ~/nam_repos/nam</code></p>
<p>start uninstall process:</p>
<p><code>make clean</code></p>
<br>
<p>note: latest version is - v1.0.0unstable. There may be a few bugs</p>
