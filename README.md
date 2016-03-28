# quickopenvpn

## Install

Run 'python install.py' in command line. Follow the instructions.


## Run

  After installation open **srv.py** with text editor and change *ipadr* and *org*
to yours. Change *CERTDIR* if you change path to CA from default.
  **install.py** returns openvpn server config (server.conf). You can start openvpn with 
by 
```
sudo openvpn --config path_to_server.conf
```
  Installation script creates start and stop shell scripts for CA Web Interface. 
You can run backend with ./start and stop it by ./stop. Web interface available 
at 
```
https://ipard(or_your_domain):4443/
```

