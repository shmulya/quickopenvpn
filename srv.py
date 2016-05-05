import BaseHTTPServer, SimpleHTTPServer
import ssl, subprocess, json, re, os, logging, yaml, md5, Cookie
from urllib import unquote

class certmgr():

    def certlist(self,testsuit=None):
        
        def tt_of_cert(sn,st):
            
            def revtime(sn):
                fl = False
                tmp = []
                rvtime = ''
                crl = subprocess.check_output("openssl crl -text -in '%s/crl.pem' -noout"%CERTDIR, shell = True)
                crl = crl.split('\n')
                for row in crl:
                    if fl == True:
                        tmp = row.split(' ')
                        rvtime = tmp[10]+" "+tmp[11]+" "+ tmp[12]+" "+tmp[13]+" "+tmp[14]
                        return rvtime
                        break
                    srch = re.search('Serial Number: %s'%sn, row)
                    if srch != None:
                        fl = True
                    
            tt = subprocess.check_output("openssl x509 -text -in '%s/%s.pem' -noout | grep 'TLS' | awk '{print($3)}'"%(CERTDIR,sn), shell=True)
            bf = subprocess.check_output("openssl x509 -text -in '%s/%s.pem' -noout | grep 'Not Before' | awk '{print($3,$4,$5,$6,$7)}'"%(CERTDIR,sn), shell=True)
            if st == 'V':
                af = subprocess.check_output("openssl x509 -text -in '%s/%s.pem' -noout | grep 'Not After :' | awk '{print($4,$5,$6,$7,$8)}'"%(CERTDIR,sn), shell=True)
                return (bf[:-1],af[:-1],tt[:-1])
            if st == 'R':
                af = revtime(sn)
                return (bf[:-1],af,tt[:-1])
            
        
        if testsuit == None:
            crtbase = open(CERTDIR+'/index.txt','r')
        else:
            crtbase = testsuit
        crtinfolist = []
        crtlist = []
        for line in crtbase:
            crtinfolist.append(line.split())
        n = 0
        for el in crtinfolist:
            if crtinfolist[n][0] == 'V':
                crtinfolist[n][4] = el[4][1:].split('/')
                flnm = crtinfolist[n][4][2].split('=')[1]
                if os.path.exists('%s/arc/%s.tar'%(CERTDIR,flnm)) == True:
                    crtinfolist[n].append('1')
                else:
                    crtinfolist[n].append('0')
                n = n + 1
            elif crtinfolist[n][0] == 'R':
                crtinfolist[n][5] = el[5][1:].split('/')
                crtinfolist[n].append('0')
                n = n + 1
        for str in crtinfolist:
            if str[0] == 'V':
                (bf,af,tt) = tt_of_cert(str[2],str[0])
                crtlist.append([str[0],str[2],str[4],str[5],bf,af,tt])
            elif str[0] == 'R':
                (bf,af,tt) = tt_of_cert(str[3],str[0])
                crtlist.append([str[0],str[3],str[5],str[6],bf,af,tt])
        return crtlist
    
    
    def certgen(self,cn,f,typ,o,c='RU', csr=None):
    
        def userconfig(cn):
            tmpl = open('%s/data/templates/client.conf'%WORKDIR,'r').read()
            conf = open('%s/%s.conf'%(CERTDIR,cn),'w')
            conf.write(tmpl%(vpnip,cn,cn,cn,cn,cn,cn))
            conf.close()
        fl = False
        if f == '0':
            res = subprocess.call('openssl genrsa -out "%s/%s.key"'%(CERTDIR,cn),shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
            if res == 0:
                logging.debug('Private key for %s created'%cn)
            elif res == 1:
                logging.error("Can't create private key for "+cn)
            res = subprocess.call('openssl req -new -nodes -config "%s/openssl.cnf" -key "%s/%s.key" -out "%s/%s.csr" -subj "/C=%s/O=%s/CN=%s"'%(CERTDIR,CERTDIR,cn,CERTDIR,cn,c,o,cn),shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
            userconfig(cn)
            if typ == 'srv':
                ext = '-extensions server'
            elif typ == 'clnt':
                ext = '-extensions usr_cert'
            res = subprocess.call('openssl ca -batch %s -config "%s/openssl.cnf" -in "%s/%s.csr" -notext -out "%s/%s.crt"'%(ext,CERTDIR,CERTDIR,cn,CERTDIR,cn),shell=True, stdout=open('./log/crt.log', 'a'), stderr=subprocess.STDOUT)
            if res == 0:
                logging.debug('Certificate for %s signed'%cn)
                fl = True
                res = subprocess.call('rm -rf "%s/%s.csr"'%(CERTDIR,cn),shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
                res = subprocess.call('cd "%s" && tar -cvf arc/%s.tar %s.* ca.crt ta.key'%(CERTDIR,cn,cn),shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
                res = subprocess.call('rm -rf %s/%s.*'%(CERTDIR.replace(' ', '\ '),cn),shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
            elif res == 1:
                fl = False
                logging.error("Can't sign certificate for "+cn)
        if f == '1':
            file = open('./tmp/%s.csr'%cn,'w')
            print unquote(csr)
            n = 0
            str = ''
            for lin in unquote(csr).split('\n'):
                n = n + 1
                if n == 1 or n == len(unquote(csr).split('\n')):
                    lin = lin.replace('+',' ')
                str = str + lin + '\n'
            file.write(str)
            file.close()
            if typ == 'srv':
                ext = '-extensions server'
            elif typ == 'clnt':
                ext = '-extensions usr_cert'
            res = subprocess.call('openssl ca -batch %s -config "%s/openssl.cnf" -in "%s/tmp/%s.csr" -out "%s/%s.crt"'%(ext,CERTDIR,cn,WORKDIR,CERTDIR,cn),shell=True, stdout=open('./log/crt.log', 'a'), stderr=subprocess.STDOUT)
            if res == 1:
                fl = False
                logging.error("Can't sign certificate for "+cn)
            else:
                fl = True
                logging.debug('Certificate for %s signed'%cn)
                res = subprocess.call('cd "%s" && tar -cvf arc/%s.tar %s.* ca.crt ta.key'%(CERTDIR,cn,cn),shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
                res = subprocess.call('rm -rf %s/tmp/%s.csr'%(WORKDIR.replace(' ', '\ '),cn),shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
        return fl
                
    def revoke(self,sn,cn):
        res = subprocess.call('openssl ca -config "%s/openssl.cnf" -revoke "%s/%s.pem"'%(CERTDIR,CERTDIR,sn), shell=True, stdout=open('./log/crt.log', 'a'), stderr=subprocess.STDOUT)
        if res == 1:
            fl = False
            logging.error("Can't revoke certificate for "+cn)
        else:
            fl = True
            logging.debug('Certificate for %s revoked'%cn)
        res = subprocess.call('openssl ca -config "%s/openssl.cnf" -gencrl -out "%s/crl.pem"'%(CERTDIR,CERTDIR), shell=True, stdout=open('./log/crt.log', 'a'), stderr=subprocess.STDOUT)
        if res == 1:
            fl = False
        else:
            fl = True
        res = subprocess.call('rm -rf %s/arc/%s.tar'%(CERTDIR.replace(' ', '\ '),cn),shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
        return fl

class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        srch = re.search('(.js$)|(.css$)|(images)', self.path)
        if srch != None:
            srch1 = re.search('.js$', self.path)
            if srch1 != None:
                try:
                    self.response(self, open(WORKDIR+'/data/pages'+self.path,'rb').read(), type='text/javascript')
                except IOError:
                    self.response(self, open(WORKDIR+'/data/pages/404.html','r').read(), 404)
            srch2 = re.search('.css$', self.path)
            if srch2 != None:
                try:
                    self.response(self, open(WORKDIR+'/data/pages'+self.path,'rb').read(), type='text/css')
                except IOError:
                    self.response(self, open(WORKDIR+'/data/pages/404.html','r').read(), 404)
            srch3 = re.search('images/[\w\s]+', self.path)
            if srch3 != None:
                try:
                    self.response(self, open(WORKDIR+'/data/pages'+self.path,'rb').read(), type='image/jpeg')
                except IOError:
                    self.response(self, open(WORKDIR+'/data/pages/404.html','r').read(), 404)
            else:
                srch31 = re.search('images/$', self.path)
                if srch31 != None:
                    self.response(self, open(WORKDIR+'/data/pages/403.html','r').read(), 403)
        if self.headers.get('Cookie') is None and srch == None:
            self.response(self,open(WORKDIR+'/data/pages/md5jq.html','r').read())
        elif self.headers.get('Cookie') != None:
            vercook = Cookie.BaseCookie()
            vercook.load(self.headers.get('Cookie'))
            hsver = md5.new()
            hsver.update('%s %s'%(self.headers.get('User-Agent'),self.client_address[0]))
            for k,v in vercook.iteritems():
                if k == 'restricted_cookie':
                    if v.value == hsver.hexdigest():
                        if os.path.exists(WORKDIR+'/session/'+hsver.hexdigest()) == True:
                            if self.path == '/' or self.path == '/index.html':
                                self.response(self,open(WORKDIR+'/data/pages/index.html','r').read())
                            srch = re.search('arc/[\w\s]+', self.path)
                            if srch != None:
                                try:
                                    self.response(self, open(CERTDIR+self.path,'rb').read(), type='application/x-tar')
                                except IOError: 
                                    self.response(self, open(WORKDIR+'/data/pages/404.html','r').read(), 404)
                            else:
                                srch01 = re.search('arc/$', self.path)
                                if srch01 != None:
                                    self.response(self, open(WORKDIR+'/data/pages/403.html','r').read(), 403)
                        else:
                            self.response(self, 'Session file is not found')
                else:
                    self.response(self, 'Cookie is not valid')
                    
    def do_POST(self):
        
        if self.path == '/login':
            content_len = int(self.headers.getheader('content-length', 0))
            post_body = self.rfile.read(content_len)
            post_body = post_body.split('&')
            req = []
            for it in post_body:
                f = it.split('=')
                req.append(f[1])
            if req[0] == passwd:
                self.send_response(200)
                sesid = md5.new()
                sesid.update('%s %s'%(self.headers.get('User-Agent'),self.client_address[0]))
                self.send_header('Set-Cookie', 'restricted_cookie=%s; Domain=%s; Max-Age=600'%(sesid.hexdigest(),self.headers.get('Host').split(':')[0]))
                self.end_headers()
                sesidfile = open(WORKDIR+'/session/'+sesid.hexdigest(),'w')
                sesidfile.close()
        else:
            if self.headers.get('Cookie') is None and self.path != '/login':
                self.send_header('Content type', 'text/html')
                self.end_headers()
                self.wfile.write('Unauthorized')
            elif self.headers.get('Cookie') != None:
                vercook = Cookie.BaseCookie()
                vercook.load(self.headers.get('Cookie'))
                hsver = md5.new()
                hsver.update('%s %s'%(self.headers.get('User-Agent'),self.client_address[0]))
                for k,v in vercook.iteritems():
                    if k == 'restricted_cookie':
                        if v.value == hsver.hexdigest():
                            if os.path.exists(WORKDIR+'/session/'+hsver.hexdigest()) == True:
                                if self.path == '/api':
                                    manager = certmgr()
                                    content_len = int(self.headers.getheader('content-length', 0))
                                    post_body = self.rfile.read(content_len)
                                    post_body = post_body.split('&')
                                    req = []
                                    for it in post_body:
                                        f = it.split('=')
                                        req.append(f[1])
                                    try:
                                        if req[0] == 'crtget':
                                            self.response(self, json.dumps(manager.certlist()), type='application/json')
                                        elif req[0] == 'crtgen':
                                            if req[2] == '0': 
                                                res = manager.certgen(req[1],req[2],req[3],org)
                                                if res == True:
                                                    logging.debug('New certificate for CN=%s created'%req[1])
                                                    self.response(self,'Done')
                                                else:
                                                    logging.error('Can\'t create new certificate and key, CN is '+req[1])
                                                    self.response(self,'Error, see server log', 500)
                                            elif req[2] == '1':
                                                res = manager.certgen(req[1],req[2],req[3],org,csr=req[4])
                                                if res == True:
                                                    logging.debug('Certificate from csr for CN=%s created'%req[1])
                                                    self.response(self,'Done')
                                                else:
                                                    logging.error('Can\'t sign certificate from csr, CN is '+req[1])
                                                    self.response(self,'Error, see server log', 500)
                                        elif req[0] == 'crtrev':
                                            res = manager.revoke(req[1],req[2])
                                            if res == True:
                                                logging.debug('Certificate for CN=%s revoked'%req[2])
                                                self.response(self, 'Done')
                                            else:
                                                logging.error('Can\'t revoke certificate, CN is '+req[2])
                                                self.response(self,'Error, see server log', 500)
                                    #except Exception:
                                    #    pass
                                    except IndexError:
                                        logging.error('Check arguments in post request from client, post body is %s'%post_body)
                                        self.response(self, 'Error, see server log', 500)
                            else:
                                self.response(self, 'Session file is not found')
                        else:
                            self.response(self, 'Password incorrect')
                    else:
                        self.end_headers()
                        self.wfile.write('Cookie is not valid')
                
    def log_message(self, format, *args):
        logstr = '[%s] - %s %s\n'%(self.log_date_time_string(),self.address_string(),format%args)
        logging.debug(logstr)

    def response(self, cl,cont,resp=200,type='text/html'):
        cl.send_response(resp)
        cl.send_header("Content-type", type)
        cl.end_headers()
        cl.wfile.write(cont)

runpath = os.getcwd()

if os.path.exists(runpath+'/config') == True:
    
    conf = open('%s/config'%runpath,'r').read()
    config = yaml.load(conf)
    WORKDIR = config.get('WORKDIR')
    CERTDIR = config.get('CERTDIR')
    certFile = config.get('sslcrt')
    ipadr = config.get('ipadr')
    vpnip = config.get('vpnip')
    org = config.get('org')
    passwd = config.get('password')
    logging.basicConfig(format='[%(levelname)s] [%(asctime)s] - %(message)s', filename=WORKDIR+'/log/crt.log', level=logging.WARN)
    
    if __name__ == '__main__':
        httpd = BaseHTTPServer.HTTPServer((ipadr, 4443), MyHandler)
        
        httpd.socket = ssl.wrap_socket (httpd.socket, certfile='ca/sslcert.pem', server_side=True)
        httpd.serve_forever()
else:
    print '======================================='
    print 'Can\'t find config file. Check that it exists and srv.py started from directory where it placed. Also you can start it by ./start'
    print '======================================='

