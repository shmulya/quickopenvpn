import BaseHTTPServer, SimpleHTTPServer
import ssl, subprocess, json, re, os, logging
#from twisted.test.test_hook import subPost
from urllib import unquote


WORKDIR = os.getcwd()
CERTDIR = WORKDIR+'/ca' # DO NOT CHANGE IF DEFAULT INSTALL path to your certificate storage (keystorage from install)
ipadr = '127.0.0.1' #IP for HTTPS connection
org = 'Shmula.inc' #Your company
certFile = CERTDIR+'/sslcert.pem'
logging.basicConfig(format='[%(levelname)s] [%(asctime)s] - %(message)s', filename=WORKDIR+'/log/crt.log', level=logging.WARN)


def userconfig(cn):
    tmpl = open('%s/data/templates/client.conf'%WORKDIR,'r').read()
    conf = open('%s/%s.conf'%(CERTDIR,cn),'w')
    conf.write(tmpl%(ipadr,cn,cn,cn,cn,cn,cn))
    conf.close()

def certlist():
    crtbase = open(CERTDIR+'/index.txt','r')
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

def response(cl,cont,resp=200,type='text/html'):
    cl.send_response(resp)
    cl.send_header("Content-type", type)
    cl.end_headers()
    cl.wfile.write(cont)

def tt_of_cert(sn,st):
    tt = subprocess.check_output("openssl x509 -text -in '%s/%s.pem' -noout | grep 'TLS' | awk '{print($3)}'"%(CERTDIR,sn), shell=True)
    bf = subprocess.check_output("openssl x509 -text -in '%s/%s.pem' -noout | grep 'Not Before' | awk '{print($3,$4,$5,$6,$7)}'"%(CERTDIR,sn), shell=True)
    if st == 'V':
        af = subprocess.check_output("openssl x509 -text -in '%s/%s.pem' -noout | grep 'Not After :' | awk '{print($4,$5,$6,$7,$8)}'"%(CERTDIR,sn), shell=True)
        return (bf[:-1],af[:-1],tt[:-1])
    if st == 'R':
        af = revtime(sn)
        return (bf[:-1],af,tt[:-1])

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

def certgen(cn,f,typ,c='RU',o=org, csr=None):
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
            
def revoke(sn,cn):
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
        if self.path == '/':
            response(self,open(WORKDIR+'/data/pages/index.html','r').read())
        elif self.path == '/crl.pem':
            response(self, open(CERTDIR+'/crl.pem','rb').read(), type='application/x-pem-file')
        srch = re.search('arc/', self.path)
        if srch != None:
            response(self, open(CERTDIR+self.path,'rb').read(), type='application/x-tar')
        srch1 = re.search('.js$', self.path)
        if srch1 != None:
            response(self, open(WORKDIR+'/data/pages/'+self.path,'rb').read(), type='text/javascript')
        srch2 = re.search('images', self.path)
        if srch2 != None:
            response(self, open(WORKDIR+'/data/pages/'+self.path,'rb').read(), type='image/jpeg')
        srch3 = re.search('.css$', self.path)
        if srch3 != None:
            response(self, open(WORKDIR+'/data/pages/'+self.path,'rb').read(), type='text/css')        
    def do_POST(self):
        if self.path == '/api':
            content_len = int(self.headers.getheader('content-length', 0))
            post_body = self.rfile.read(content_len)
            post_body = post_body.split('&')
            req = []
            for it in post_body:
                f = it.split('=')
                req.append(f[1])
            try:
                if req[0] == 'crtget':
                    response(self, json.dumps(certlist()), type='application/json')
                elif req[0] == 'crtgen':
                    if req[2] == '0': 
                        res = certgen(req[1],req[2],req[3])
                        if res == True:
                            logging.debug('New certificate for CN=%s created'%req[1])
                            response(self,'Done')
                        else:
                            logging.error('Can\'t create new certificate and key, CN is '+req[1])
                            response(self,'Error, see server log', 500)
                    elif req[2] == '1':
                        res = certgen(req[1],req[2],req[3],csr=req[4])
                        if res == True:
                            logging.debug('Certificate from csr for CN=%s created'%req[1])
                            response(self,'Done')
                        else:
                            logging.error('Can\'t sign certificate from csr, CN is '+req[1])
                            response(self,'Error, see server log', 500)
                elif req[0] == 'crtrev':
                    res = revoke(req[1],req[2])
                    if res == True:
                        logging.debug('Certificate for CN=%s revoked'%req[2])
                        response(self, 'Done')
                    else:
                        logging.error('Can\'t revoke certificate, CN is '+req[2])
                        response(self,'Error, see server log', 500)
            #except Exception:
            #    pass
            except IndexError:
                logging.error('Check arguments in post request from client, post body is %s'%post_body)
                response(self, 'Error, see server log', 500)
    def log_message(self, format, *args):
        logstr = '[%s] - %s %s\n'%(self.log_date_time_string(),self.address_string(),format%args)
        logging.debug(logstr)

if os.path.exists(WORKDIR+'/data') == True:
    
    httpd = BaseHTTPServer.HTTPServer((ipadr, 4443), MyHandler)
    
    httpd.socket = ssl.wrap_socket (httpd.socket, certfile=certFile, server_side=True)
    httpd.serve_forever()
else:
    print '==================================================================================='
    print 'Can\'t find data directory. Check that srv.py started from directory where it placed'
    print '==================================================================================='