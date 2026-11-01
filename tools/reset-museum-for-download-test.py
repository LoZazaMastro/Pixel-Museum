#!/usr/bin/env python3
"""Plan a PPSA70421-only first-run reset. Nothing is deleted without BOTH flags."""
from pathlib import Path,PurePosixPath
from ftplib import FTP,error_perm,error_temp,error_proto
import argparse,errno,json,posixpath,socket,time

TITLE='PPSA70421'
HOST='192.168.1.56'
PORT=2121
APP='/data/homebrew/PPSA70421'
USER='/user/download/PPSA70421'
COLLECTION='/data/pixelmuseum'
NOTIFICATIONS='/data/pixel-museum-notifications'
# The closed title's /download0/pixelmuseum is inside this title-exclusive
# download0.dat. Never substitute /user/download itself or another title ID.
ALLOWLIST=(APP,USER,COLLECTION,NOTIFICATIONS)
NOTIFICATION_NAMES={name+'.png' for name in (
 'first_culture','maximum_zoom','exp_invaders','exp_pacman','exp_tetris',
 'exp_katamari','first_today','first_video','first_music','exp_mario',
 'exp_celeste','first_pin_3d','secret_05')}
ROOT=Path(__file__).resolve().parents[1]
SERVER_COMMAND_SOURCE='https://raw.githubusercontent.com/RuiNelson/ftpsrv-streamextract/master/README.md'

def canonical(path):
    if not isinstance(path,str)or not path.startswith('/')or'//'in path or any(c in path for c in '\r\n\x00\\')or posixpath.normpath(path)!=path:
        raise ValueError('Noncanonical FTP path rejected: '+repr(path))
    return path

def allowed(path):
    canonical(path)
    if not any(path==root or path.startswith(root+'/')for root in ALLOWLIST):raise ValueError('Outside the exact museum allowlist: '+path)
    return path

def child(directory,name):
    if not name or name in{'.','..'}or'/'in name or any(c in name for c in '\r\n\x00\\'):raise ValueError('Unsafe FTP entry name')
    return allowed(directory+'/'+name)

def missing(error):
    message=str(error).lower()
    return str(error).startswith('550')and any(word in message for word in ('no such','not found','does not exist'))

def entry_type(facts):
    kind=facts.get('type','').lower()
    if 'link'in kind or'slink'in kind:raise ValueError('Symbolic FTP link is not followed')
    mode=facts.get('unix.mode')
    if mode:
        try:
            if int(mode,8)&0o170000==0o120000:raise ValueError('Symbolic Unix link is not followed')
        except (TypeError,ValueError)as error:
            if 'Symbolic'in str(error):raise
            raise ValueError('Invalid Unix mode')
    if kind not in{'dir','file','cdir','pdir'}:raise ValueError('Unknown MLSD type: '+kind)
    return kind

class Session:
    def __init__(self,report):self.ftp=None;self.report=report;self.reconnections=0
    def connect(self):
        self.close();self.ftp=FTP();self.ftp.connect(HOST,PORT,timeout=20);self.ftp.login('anonymous','codex');self.ftp.cwd('/')
        if self.ftp.pwd()!='/':raise RuntimeError('Unexpected FTP root')
    def close(self):
        if self.ftp:
            try:self.ftp.quit()
            except Exception:self.ftp.close()
            self.ftp=None
    def call(self,fn):
        while True:
            try:
                if self.ftp is None:self.connect()
                return fn(self.ftp)
            except (error_temp,error_proto,EOFError,TimeoutError,ConnectionError,socket.timeout,OSError)as error:
                # Two reconnects for the WHOLE run, not two for every file.
                if self.reconnections>=2:raise
                self.reconnections+=1;self.report['reconnections'].append({'attempt':self.reconnections,'error':str(error)})
                self.close();time.sleep(.25);self.connect()
    @staticmethod
    def cwd(ftp,path):
        canonical(path);ftp.cwd(path)
        if ftp.pwd()!=path:raise ValueError('FTP PWD alias mismatch: '+path+' -> '+ftp.pwd())
    def listing(self,path):
        allowed(path)
        def op(ftp):
            self.cwd(ftp,path);rows=list(ftp.mlsd());current=[facts for name,facts in rows if name=='.'and facts.get('type')=='cdir']
            if len(current)>1:raise ValueError('Ambiguous directory metadata')
            return rows,current[0].get('unique')if current else None
        return self.call(op)
    def small_file(self,path,maximum=16384):
        allowed(path)
        def op(ftp):
            self.cwd(ftp,posixpath.dirname(path));data=bytearray()
            def consume(chunk):
                if len(data)+len(chunk)>maximum:raise ValueError('Bounded metadata read exceeded')
                data.extend(chunk)
            ftp.retrbinary('RETR '+posixpath.basename(path),consume);return bytes(data)
        return self.call(op)
    def mutate(self,action,path,identity):
        allowed(path);directory=posixpath.dirname(path);name=posixpath.basename(path)
        def op(ftp):
            self.cwd(ftp,directory)
            # MLSD gives link-aware type/unique metadata. Never CWD into a file,
            # a link, a virtual alias, or an entry of an unknown type.
            response=ftp.sendcmd('MLST '+name)
            factlines=[line.strip()for line in response.splitlines()if'type='in line.lower()and';'in line]
            if len(factlines)!=1:raise ValueError('Cannot revalidate target metadata: '+path)
            factstring=factlines[0].split(' ',1)[0];facts={k.lower():v for field in factstring.split(';')if'='in field for k,v in[field.split('=',1)]}
            kind=entry_type(facts)
            if kind!=('file'if action=='DELE'else'dir'):raise ValueError('Target type changed before deletion: '+path)
            if identity and facts.get('unique')and identity!=facts['unique']:raise ValueError('Target identity changed: '+path)
            return ftp.delete(name)if action=='DELE'else ftp.rmd(name)
        return self.call(op)
    def stat(self,path):
        allowed(path)
        def op(ftp):
            self.cwd(ftp,posixpath.dirname(path));response=ftp.sendcmd('MLST '+posixpath.basename(path))
            lines=[line.strip()for line in response.splitlines()if'type='in line.lower()and';'in line]
            if len(lines)!=1:raise ValueError('Cannot validate target metadata: '+path)
            return{k.lower():v for field in lines[0].split(' ',1)[0].split(';')if'='in field for k,v in[field.split('=',1)]}
        return self.call(op)
    def remove_tree(self,path,identity,timeout=600):
        if path not in ALLOWLIST:raise ValueError('RMDA is restricted to the exact museum roots')
        facts=self.stat(path)
        if entry_type(facts)!='dir'or(identity and facts.get('unique')and identity!=facts['unique']):raise ValueError('Recursive target identity/type changed')
        # sendcmd may time out after the server accepted the asynchronous work.
        # Never automatically resend RMDA in that ambiguous case.
        while True:
            try:response=self.ftp.sendcmd('RMDA '+path);break
            except error_temp as error:
                # Explicit 450 means the command was NOT accepted (for example
                # another background operation is still running). Retry only
                # after a fresh session and exact identity revalidation.
                if not str(error).startswith('450')or self.reconnections>=2:raise
                self.reconnections+=1;self.report['reconnections'].append({'attempt':self.reconnections,'error':str(error),'rmda_explicitly_rejected':True});time.sleep(.25);self.connect();facts=self.stat(path)
                if entry_type(facts)!='dir'or(identity and facts.get('unique')and identity!=facts['unique']):raise ValueError('Target changed after reconnect')
            except (EOFError,TimeoutError,ConnectionError,socket.timeout,OSError)as error:
                if self.reconnections>=2:raise
                self.reconnections+=1;self.report['reconnections'].append({'attempt':self.reconnections,'error':str(error),'rmda_resubmitted':False});self.connect();response='connection lost after RMDA; checking completion without resubmitting';break
        deadline=time.monotonic()+timeout;polls=0
        while time.monotonic()<deadline:
            try:
                facts=self.stat(path);polls+=1
                if entry_type(facts)!='dir'or(identity and facts.get('unique')and identity!=facts['unique']):raise ValueError('Recursive target changed during deletion')
            except error_perm as error:
                if missing(error):return{'response':response,'absence_verified':True,'polls':polls}
                raise
            time.sleep(.25)
        raise RuntimeError('Recursive deletion did not reach verified absence; later targets left untouched')

def plan_tree(session,path,actions,seen,root):
    rows,identity=session.listing(path)
    if path==COLLECTION:
        # This root belongs only to the downloadable museum collection. Refuse
        # a name collision instead of deleting an unrelated tree at this path.
        for name,facts in rows:
            if name not in {'.','..'} and(name!='collection' or entry_type(facts)!='dir'):
                raise ValueError('Unrecognized collection storage root entry: '+name)
    if identity:
        if identity in seen:raise ValueError('Repeated directory identity/link rejected: '+path)
        seen.add(identity)
    for name,facts in rows:
        kind=entry_type(facts)
        if kind in{'cdir','pdir'}:
            if name not in{'.','..'}:raise ValueError('Unexpected virtual metadata entry')
            continue
        remote=child(path,name)
        if root==NOTIFICATIONS and(name not in NOTIFICATION_NAMES or kind!='file'):raise ValueError('Unconfirmed notification cache entry: '+remote)
        if kind=='dir':plan_tree(session,remote,actions,seen,root)
        else:
            size=facts.get('size')
            if size is None or not size.isdecimal():raise ValueError('Missing exact file size: '+remote)
            actions.append({'action':'DELE','path':remote,'bytes':int(size),'unique':facts.get('unique')})
    actions.append({'action':'RMD','path':path,'unique':identity})

def make_plan(session,report):
    for command in ('FEAT','HELP','SITE HELP'):
        try:report['ftp_help'][command]=session.call(lambda ftp:ftp.sendcmd(command))
        except error_perm as error:report['ftp_help'][command]=str(error)
    # An installed app must prove its title ID before the app tree is touched.
    try:
        param=json.loads(session.small_file(APP+'/sce_sys/param.json'))
        if param.get('titleId')!=TITLE:raise ValueError('Application identity does not match PPSA70421')
        report['application_identity']={'titleId':param['titleId'],'contentId':param.get('contentId')}
    except error_perm as error:
        if not missing(error):raise
        report['application_identity']={'status':'missing'}
    for root in report.get('delete_roots',ALLOWLIST):
        target={'path':root,'actions':[]};report['targets'].append(target)
        try:
            plan_tree(session,root,target['actions'],set(),root)
            if root==USER:
                files=[row for row in target['actions']if row['action']=='DELE']
                # Known title-exclusive container or exposed title-owned tree;
                # no paths outside this title's own download directory are allowed.
                target['userdata_kind']='closed title download0.dat container'if any(row['path']==USER+'/download0.dat'for row in files)else'exposed title directory'
            target.update(status='planned',files=sum(row['action']=='DELE'for row in target['actions']),directories=sum(row['action']=='RMD'for row in target['actions']),bytes=sum(row.get('bytes',0)for row in target['actions']))
        except error_perm as error:
            target['actions']=[];target['status']='missing'if missing(error)else'inaccessible';target['error']=str(error)
        except (ValueError,RuntimeError)as error:
            target['actions']=[];target['status']='blocked';target['error']=str(error)
    report['recursive_server_delete']=False
    report['recursive_server_delete_reason']='HELP names RMDA/SITE RMDIR but does not document recursion/link semantics; use revalidated DELE/RMD only.'

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');parser.add_argument('--app-closed',action='store_true');parser.add_argument('--keep-app',action='store_true',help='Remove only this museum\'s data and caches; preserve the application payload');parser.add_argument('--server-recursive',action='store_true',help='Use the documented RMDA command after a complete link-free preflight; wait for absence between roots');parser.add_argument('--report',type=Path,default=ROOT/'build/research/download-first-run-reset-20261031/reset-plan.json');args=parser.parse_args()
    if args.execute and not args.app_closed:parser.error('--execute requires the explicit --app-closed flag')
    report={'status':'PLANNING','host':HOST,'port':PORT,'title_id':TITLE,'execute':args.execute,'allowlist':list(ALLOWLIST),'ftp_help':{},'targets':[],'reconnections':[],'results':[],'counts':{'deleted_files':0,'deleted_directories':0,'already_missing':0,'errors':0},'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    report['delete_roots']=[root for root in ALLOWLIST if not(args.keep_app and root==APP)]
    report['application_preserved']=args.keep_app
    args.report.parent.mkdir(parents=True,exist_ok=True);session=Session(report)
    try:
        if args.execute:
            active=session.call(lambda ftp:[name for name,_ in ftp.mlsd('/proc')if TITLE in name.upper()])
            report['active_title_processes']=active
            if active:raise RuntimeError('Pixel Museum is still running; no deletion performed')
        make_plan(session,report)
        if args.server_recursive:
            if 'RMDA'not in report['ftp_help'].get('HELP','').split():raise RuntimeError('This FTP server does not advertise RMDA')
            report['recursive_server_delete']=True;report['recursive_server_delete_source']=SERVER_COMMAND_SOURCE;report['recursive_server_delete_reason']='Primary server documentation explicitly defines RMDA as tree deletion; live HELP advertises it. Full MLSD preflight rejects links; roots processed sequentially to verified absence.'
        report['status']='PLAN_ONLY';args.report.write_text(json.dumps(report,indent=2),encoding='utf8')
        if args.execute:
            if any(target['status']in{'blocked','inaccessible'}for target in report['targets']):raise RuntimeError('Unsafe/inaccessible target found; no deletions performed')
            report['status']='EXECUTING';args.report.write_text(json.dumps(report,indent=2),encoding='utf8')
            journal=args.report.with_suffix('.deleted.jsonl')
            with journal.open('a',encoding='utf8')as log:
                for target in report['targets']:
                    if args.server_recursive and target['status']=='planned':
                        root_action=target['actions'][-1]
                        proof=session.remove_tree(target['path'],root_action.get('unique'))
                        for action in target['actions']:
                            result={k:v for k,v in action.items()if k in{'action','path','bytes'}};result['status']='deleted_by_server_recursive';report['results'].append(result);log.write(json.dumps(result)+'\n');report['counts']['deleted_files'if action['action']=='DELE'else'deleted_directories']+=1
                        target['deletion_proof']=proof;log.flush();print(json.dumps({'removed':target['path'],**report['counts']}),flush=True)
                        continue
                    for action in target['actions']:
                        result={k:v for k,v in action.items()if k in{'action','path','bytes'}}
                        try:
                            session.mutate(action['action'],action['path'],action.get('unique'));result['status']='deleted';report['counts']['deleted_files'if action['action']=='DELE'else'deleted_directories']+=1
                        except error_perm as error:
                            result.update(status='already_missing'if missing(error)else'error',error=str(error));report['counts']['already_missing'if missing(error)else'errors']+=1
                        except (error_temp,error_proto,EOFError,OSError,ValueError,RuntimeError)as error:
                            result.update(status='error',error=str(error));report['counts']['errors']+=1
                        report['results'].append(result);log.write(json.dumps(result)+'\n')
                        if len(report['results'])%64==0:log.flush()
                        if len(report['results'])%512==0:print(json.dumps({'completed':len(report['results']),**report['counts']}),flush=True)
            if args.keep_app and not report['counts']['errors'] and report.get('application_identity',{}).get('titleId')==TITLE:
                # Clear every downloaded byte, but retain the empty system-owned
                # parent needed when launching an already registered title.
                # Never create a download image ourselves; the console formats it.
                def restore_parent(ftp):
                    try:ftp.mkd(USER)
                    except error_perm as error:
                        if 'exist'not in str(error).lower():raise
                    matches=[facts for name,facts in ftp.mlsd('/user/download')if name==TITLE]
                    if len(matches)!=1 or entry_type(matches[0])!='dir':raise RuntimeError('Unsafe reset download parent')
                    ftp.sendcmd('SITE CHMOD 0700 '+USER)
                    rows=list(ftp.mlsd(USER))
                    if any(name not in{'.','..'}for name,_ in rows):raise RuntimeError('Reset download parent is not empty')
                    return {'path':USER,'empty':True,'mode':'0700','download_image_created':False}
                report['retained_download_parent']=session.call(restore_parent)
            report['status']='PASS_REMOVED_MUSEUM_ONLY'if not report['counts']['errors']else'PARTIAL_REVIEW_ERRORS'
        report['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    except Exception as error:
        report['status']='FAILED';report['error']=str(error)
    finally:session.close();args.report.write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({'status':report['status'],'execute':report['execute'],'targets':[{k:v for k,v in target.items()if k!='actions'}for target in report['targets']],'counts':report['counts'],'report':str(args.report)},indent=2))
    return 0 if report['status']in{'PLAN_ONLY','PASS_REMOVED_MUSEUM_ONLY'}else 1
if __name__=='__main__':raise SystemExit(main())
