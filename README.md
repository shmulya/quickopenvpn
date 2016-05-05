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
in command line. Follow the instructions.


## Run

  **install.py** returns openvpn server config (server.conf) and installing CA
server with web interface. You can start openvpn with
```
sudo openvpn --config path_to_server.conf
```
  If you used autoconfig during install OpenVPN server will be started automaticaly.
  Installation script creates start and stop shell scripts for CA Web Interface, and 
config file *config* in work directory. You can run backend with ./start and stop it by
./stop. Web interface available at 
```
https://ipard(or_your_domain):4443/
```

## How to


Web interface helps to generate new user's and server's certificates. It needs to 
user authentication in OpenVPN. Also you can use server certificate for self-
signed SSL HTTPS Server.
After generate new certificate you can download tarball with user's private key,
signed certificate, openvpn client config file, CA certificate and TLS key. Check
path to files in .conf file and start openpvn with this config file. Run
```
ping 10.8.0.1
```
Congratulation, if 10.8.0.1 sent pong. See openvpn log for details. 
If you want use your openvpn server as Internet gate uncomment string
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
