import subprocess, os, yaml, re

yes = set(['yes','y', 'ye', ''])
no = set(['no','n'])
fl = False
flt = False

def loop_input(msg): # Loop user unput. You can't input empty string
    str = ""
    while str.strip() == "":
        str=raw_input(msg)
    return str

workdir = os.getcwd() 

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

    flip = False
    while flip == False:
        ipadr = loop_input('Web interface will listen IP (* or 0.0.0.0 for any interface): ')
        if ipadr == '*':
            ipadr = '0.0.0.0'
            flip = True
        else:
            res = re.search('\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', ipadr)
            if res != None:
                ipadr = res.group(0)
                flip = True
            elif res == None:
                print 'It is not IP address, try again'
                
    while fl == False:
        if os.path.exists(certdir)==False:
            res = subprocess.call('cd "%s" && mkdir log && mkdir tmp'%workdir, shell = True)
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
                res = subprocess.call('cd "%s" && mkdir log && mkdir tmp'%workdir, shell = True)
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
    o = loop_input('Organisation: ')    
    cn = loop_input('CA server name (Use your IP or domain): ')
    while len(cn) > 64:
        cn = loop_input('Max length 64 symbols, try again: ').upper()
    print 'Attempt to create CA certificate and private key...'
    res = subprocess.call('cd "%s" && openssl req -nodes -config "%s/openssl.cnf" -days 1825 -x509 -newkey rsa -keyout ca.key -out ca.crt -subj "/C=%s/O=%s/CN=%s"'%(certdir,certdir,c,o,cn), shell=True, stdout=open('./log/install.log', 'a'), stderr=subprocess.STDOUT)
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
        open(workdir+'/config','w').write('org : ' + o + '\n' + 'ipadr : ' + ipadr + '\n' + 'CERTDIR : ' + certdir + '\n' + 'sslcrt : ' + certdir+'/sslcert.pem' + '\n' + 'WORKDIR : ' + workdir)
        open(workdir+'/server.conf','w').write(file%(certdir,certdir,certdir,certdir,certdir,certdir))        
    else:
        print ''
        print 'Error, read %s/log/ for more information'%workdir
        
    cho = raw_input('Do you want to try configure and run OpenVPN server automatically? Need to be root or have a sudo. (Work in Ubuntu WITHOUT SYSTEMD): [y/n] ').lower()
    if cho in yes:
        rls = subprocess.check_output('cat /etc/*release', shell = True)
        srch = re.search('([Uu]buntu)|([Cc]ent[Oo][Ss])|(RHEL)|(rhel)', rls)
        if srch.group(0).lower() == 'ubuntu':
            res = subprocess.call('dpkg --get-selections | grep -v deinstall | grep "openvpn"', shell = True)
            if res == 0:
                res = subprocess.call('sudo mv "%s/server.conf" /etc/openvpn/openvpn_server.conf'%workdir, shell = True)
            else:
                subprocess.call('sudo apt-get install openvpn', shell = True)
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