import subprocess, os, re, getpass, md5
from __builtin__ import str

yes = set(['yes','y', 'ye', ''])
no = set(['no','n'])
fl = False
flt = False

def loop_input(msg): # Loop user unput. You can't input empty string
    str = ""
    while str.strip() == "":
        str=raw_input(msg)
    return str

def loop_password(msg):
    
    str = ""
    while str.strip() == "":
        str=getpass.getpass(msg)
    return str

workdir = os.getcwd() 

def ipcheck(rwdt):
        res = re.search('\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', rwdt)
        if res != None:
            flip = True
        elif res == None:
            flip = False
            print 'It`s not IP address, try again'
        return flip

if os.path.exists(workdir+'/data') == True:

    cho = raw_input('Use CA storage path by default [%s/ca]?: [y/n] '%workdir).lower()
    if cho in yes:
        certdir = workdir+'/ca'
    elif cho in no:
        certdir = loop_input('CA storage directory path: ')
        if certdir[-1] == '/':
            certdir = certdir[:-1]
    
    mail = loop_input('E-mail: ')
    while len(mail) > 40:
        mail = loop_input('Max length 40 symbols, try again: ').upper()

    passwd = loop_password('Password for web interface: ')
    
    ipch = False
    while ipch == False:
        ipadr = loop_input('Web interface will listen IP (* or 0.0.0.0 for any interface): ')
        if ipadr == '*':
            ipadr = '0.0.0.0'
            ipch = True
        else:
            ipch = ipcheck(ipadr)
    
    ipch = False
    while ipch == False:
        vpnipadr = loop_input('IP for incoming OpenVPN connections: ')
        ipch = ipcheck(vpnipadr)
                
    while fl == False:
        if os.path.exists(certdir)==False:
            res = subprocess.call('cd "%s" && mkdir log && mkdir tmp && mkdir session'%workdir, shell = True)
            res = subprocess.call('mkdir "%s"'%certdir, shell=True)
            res = subprocess.call('cd "%s" && rm -rf * && mkdir arc && touch serial && echo 01 > serial && touch index.txt'%(certdir), shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
            file = open('%s/data/templates/openssl.tmp'%workdir,'r').read()
            conf = open('%s/openssl.cnf'%certdir,'w')
            conf.write(file%(certdir,mail))
            conf.close()
            fl = True
        else:
            cho = raw_input('Directory %s already exist, do you want to use it (all files will be deleted)?: [y/n] '%certdir).lower()
            if cho in yes:
                res = subprocess.call('cd "%s" && mkdir log && mkdir tmp && mkdir session'%workdir, shell = True)
                res = subprocess.call('cd "%s" && rm -rf * && mkdir arc && touch serial && echo 01 > serial && touch index.txt'%(certdir), shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
                file = open('%s/data/templates/openssl.tmp'%workdir,'r').read()
                conf = open('%s/openssl.cnf'%certdir,'w')
                conf.write(file%(certdir,mail))
                conf.close()
                fl = True
            if cho in no:
                certdir = loop_input('Keystorage directory path: ')
                
    c = loop_input('Coutry code(2 symbols): ').upper()
    while len(c) > 2:
        c = loop_input('You type more than 2 symbols, try again: ').upper()
    o = loop_input('Organisation: ').replace(' ', '_')
    cn = loop_input('CA server name (Use your IP or domain): ')
    while len(cn) > 64:
        cn = loop_input('Max length 64 symbols, try again: ').upper()
    print 'Attempt to create CA certificate and private key...'
    res = subprocess.call('cd "%s" && openssl req -nodes -config "%s/openssl.cnf" -days 1825 -x509 -newkey rsa:2048 -keyout ca.key -out ca.crt -subj "/C=%s/O=%s/CN=%s"'%(certdir,certdir,c,o,cn), shell=True, stdout=open('./log/install.log', 'a'), stderr=subprocess.STDOUT)
    if res == 0:
        print 'CA certificate and private key created'
    elif res == 1:
        print "Can't create CA certificate"
    print 'Attempt to create DH2048, it can take a long time...'
    res = subprocess.call('cd "%s" && openssl dhparam -out dh2048.pem 2048'%certdir,shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
    if res == 0:
        print 'DH created'
    elif res == 1:
        print "Can't create DH"
    print 'Attempt to create TLS key...'
    res = subprocess.call('cd "%s" && openvpn --genkey --secret ta.key'%certdir,shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
    if res == 0:
        print 'TLS key created'
    elif res == 1:
        print "Can't create TLS key"
    print 'Attempt to create CRL...'
    res = subprocess.call('cd "%s" && openssl ca -config "%s/openssl.cnf" -gencrl -out crl.pem'%(certdir,certdir),shell=True, stdout=open('./log/install.log', 'a'), stderr=subprocess.STDOUT)
    if res == 0:
        print 'CRL created'
    elif res == 1:
        print "Can't create CRL"
    print 'Attempt to create OpenVPN server key...'
    res = subprocess.call('mkdir "%s/openvpn_key" && openssl genrsa -out "%s/openvpn_key/server.key"'%(certdir,certdir), shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
    if res == 0:
        print 'OpenVPN server key created'
    elif res == 1:
        print "Can't create OpenVPN server key"
    res = subprocess.call('openssl req -new -nodes -config "%s/openssl.cnf" -key "%s/openvpn_key/server.key" -out "%s/openvpn_key/server.csr" -subj "/C=%s/O=%s/CN=%s"'%(certdir,certdir,certdir,c,o,cn),shell=True, stdout=open('./log/install.log', 'a'), stderr=subprocess.STDOUT)
    print 'Attempt to sign OpenVPN server certificate...'
    res = subprocess.call('openssl ca -batch -extensions server -config "%s/openssl.cnf" -in "%s/openvpn_key/server.csr" -notext -out "%s/openvpn_key/server.crt"'%(certdir,certdir,certdir),shell=True, stdout=open('./log/install.log', 'a'), stderr=subprocess.STDOUT)
    if res == 0:
        print 'OpenVPN certificate signed'
        flt = True
    elif res == 1:
        print "Can't sign OpenVPN server certificate"
    if flt == True:
        print ''
        print 'Your openvpn config file in server.conf'
        print ''
        open(workdir+'/start','w').write('cd "%s"\npython srv.py&'%workdir)
        open(workdir+'/stop','w').write("PID=`ps aef | grep srv.py | grep -v grep | awk '{print ($1)}'`\nkill -9 $PID")
        os.chmod(workdir+'/start', 0740)
        os.chmod(workdir+'/stop', 0740)
        prks = open(certdir+'/openvpn_key/server.key','r').read()
        crts = open(certdir+'/openvpn_key/server.crt','r').read()
        str = prks + '\n' + crts
        itssl = open(certdir+'/sslcert.pem','w').write(str)
        file = open('%s/data/templates/server.conf'%workdir,'r').read()
        hash = md5.new()
        hash.update(passwd)
        open(workdir+'/config','w').write('org : ' + o + '\n' + 'ipadr : ' + ipadr + '\n' + 'CERTDIR : ' + certdir + '\n' + 'sslcrt : ' + certdir+'/sslcert.pem' + '\n' + 'WORKDIR : ' + workdir + '\n' + 'password : ' + hash.hexdigest() + '\n' + 'vpnip : ' + vpnipadr)
        open(workdir+'/server.conf','w').write(file%(certdir,certdir,certdir,certdir,certdir,certdir))  
        subprocess.call('crontab -l | { cat; echo "*/1 * * * * find %s/session/ -cmin +10 -type f -delete"; } | crontab -'%workdir, shell = 'True', stdout=open('./log/install.log', 'a'), stderr=subprocess.STDOUT)      
    else:
        print ''
        print 'Error, read %s/log/ for more information'%workdir
        
    cho = raw_input('Do you want to try configure and run OpenVPN server automatically? Need to be root or have a sudo. (Work with Ubuntu WITHOUT SYSTEMD): [y/n] ').lower()
    if cho in yes:
        rls = subprocess.check_output('cat /etc/*release', shell = True)
        srch = re.search('([Uu]buntu)', rls)
        if srch.group(0).lower() == 'ubuntu':
            res = subprocess.call('dpkg --get-selections | grep -v deinstall | grep "openvpn"', shell = True)
            if res == 0:
                res = subprocess.call('sudo mv "%s/server.conf" /etc/openvpn/openvpn_server.conf'%workdir, shell = True)
            else:
                subprocess.call('sudo apt-get install openvpn', shell = True)
                print 'Attempt to create TLS key...'
                res = subprocess.call('cd "%s" && openvpn --genkey --secret ta.key'%certdir,shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
                if res == 0:
                    print 'TLS key created'
                elif res == 1:
                    print "Can't create TLS key"
                res = subprocess.call('sudo mv "%s/server.conf" /etc/openvpn/openvpn_server.conf'%workdir, shell = True)
            if res == 0:
                res = subprocess.call('sudo update-rc.d openvpn enable 2345', shell = True)
                if res == 0:
                    print 'OpenVPN add to start after boot'
                else:
                    print 'Can`t add OpenVPN to autostart after boot'
                res = subprocess.call('sudo service openvpn start', shell = True)
                if res == 0:
                    print 'OpenVPN server started'
                    print ''
                    cho = raw_input('Do you want autoconfig Internet gate?: [y/n] ').lower()
                    if cho in yes:
                        sysctl = open('/etc/sysctl.conf')
                        sysctldict = []
                        for line in sysctl:
                            frwrd = re.search('#*net.ipv4.ip_forward=1', line)
                            if frwrd != None:
                                if line[0] == '#':
                                    frwrdfl = True
                                    sysctldict.append(line[1:])
                                else:
                                    frwrdfl = False
                                    sysctldict.append(line)
                            else:
                                if line == '\n':
                                    pass
                                else:
                                    sysctldict.append(line)
                        sysctl.close()
                        if frwrdfl == True:
                            open(workdir+'/tmp/sysctl.conf','w').write('\n'.join(sysctldict))
                            res = subprocess.call('sudo cp %s/tmp/sysctl.conf /etc/sysctl.conf && sudo chown root:root /etc/sysctl.conf && sudo sysctl -p'%workdir, shell = True, stdout=open('./log/install.log', 'a'), stderr=subprocess.STDOUT)
                            if res == 0:
                                print 'IPv4 forwarding enabled'
                            else:
                                print "Can't enable IPv4 forwarding, see logs"
                        res = subprocess.call('sudo iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o %s -j MASQUERADE && sudo iptables-save > %s/nat.conf'%(loop_input('You Internet inteface name (eth0 for example): '),workdir), shell = True, stdout=open('./log/install.log', 'a'), stderr=subprocess.STDOUT)
                        if res == 0:
                            print 'NAT enabled'
                        else:
                            print "Can't enable NAT, see logs"
                        open(workdir+'/tmp/iptables','w').write('iptables-restore < %s/nat.conf'%workdir)
                        res = subprocess.call('sudo cp %s/tmp/iptables /etc/network/if-up.d/ && sudo chown root:root /etc/network/if-up.d/iptables && sudo chmod 755 /etc/network/if-up.d/iptables'%workdir, shell = True)
                        if res == 0:
                            print 'Iptabes rules restore added to autostart on boot'
                        else:
                            print "Can't add iptables rules restor to start on boot, see logs"
                        subprocess.call('rm -rf %s/tmp/*'%workdir, shell = True)
                    else: 
                        print 'If you want to use your OpenVPN server as Internet gate open /etc/sysctl.conf with texeditor (nano for example) and uncomment line'
                        print '    net.ipv4.ip_forward=1    '
                        print 'and run'
                        print '    sudo sysctl -p'
                        print 'Add MASQUERADE rule in iptables'
                        print '    sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE'
                        print 'and save it'
                        print '    iptables-save > /etc/nat.conf'
                        print 'Create new startup script in /etc/network/if-up.d/iptables'
                        print '    sudo nano /etc/network/if-up.d/iptables'
                        print 'and insert line:'
                        print '    iptables-restore < /etc/nat.conf'
                        print 'Save and close. Change permissions to 755 owner to root for new script:'
                        print '    sudo chmod 755 /etc/network/if-up.d/iptables'
                        print '    sudo chown root:root /etc/network/if-up.d/iptables'
                        print ''
                        print 'Done!'
                else:
                    print 'Can`t start OpenVPN'
                
            else:
                print 'Error, can`t move config file to /etc/openvpn/'
            
        else:
            print 'Your disctributive is not supported'

else:
    print '=============================='
    print 'Can\'t find data directory. Check that install.py started from directory where it placed'
    print '=============================='
