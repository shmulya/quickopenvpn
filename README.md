# quickopenvpn

## Install

```
git clone https://github.com/shmulya/quickopenvpn.git
```

```
deb:
apt-get install python-pip openssl openvpn
rhel:
yum install python-pip openssl openvpn

pip install pyyaml
```
And run 
```
python install.py
```
in command line and follow the instructions.


## Run

  **install.py** returns openvpn server config (server.conf) and installing CA
server with web interface. OpenVPN server will be launch during install
```
sudo service openvpn start
```
  Installation script creates start and stop shell scripts for CA Web Interface, and 
config file *config* in work directory. You can run backend with ./start and stop it by
./stop. Web interface available at 
```
https://ipard(or_your_domain):4443/
```

## How to


Web interface helps to generate new user's and server's certificates. It required to user authentication in OpenVPN. Also you can use server certificate for self-
signed SSL HTTPS Server.
After generate new certificate you can download tarball with user's private key,
signed certificate, openvpn client config file, CA certificate and TLS key. Check
path to files in .conf file and run openpvn with this config file. Run
```
ping 10.8.0.1
```
Congratulation, if 10.8.0.1 sent pong. See openvpn log for details. 
Internet gate can be configure automaticaly during install, but you can do it by hand.
Uncomment string
```
net.ipv4.ip_forward=1
```
in **/etc/sysctl.conf** and run
```
sudo sysctl -p
```
than use iptables for configure nat
```
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```
After reboot iptables config will be reset.
