# castors_far.py : preuves de non-arret pour les machines laissees indecises par castors.c.
# Usage : ./castors 3 200 30 3000 | python3 castors_far.py
# Critere (correct) : la moitie gauche de la bande est abstraite par un automate fini D
# (au plus 3 etats, D(0)=0 lit les 0 de tete), la moitie droite est gardee exactement,
# comme une pile. Le systeme abstrait est un systeme a pile ; l'ensemble de ses
# configurations accessibles est regulier et calcule exactement par saturation (post*).
# S'il ne contient aucune configuration d'arret, la machine ne s'arrete pas.
# On essaie aussi la machine miroir (gauche et droite echangees).
import itertools, sys
BOT='#'
def parse(m):
    m=m.split(); T={}
    for i,x in enumerate(m):
        T[('ABC'[i//2],i%2)] = None if x[2]=='H' else (int(x[0]),x[1],x[2])
    return T
def mirror(T):
    return {k:(None if v is None else (v[0],'L' if v[1]=='R' else 'R',v[2])) for k,v in T.items()}
def check(T,n,delta):
    S='ABC'
    rules=[]; cnt=0
    for q in range(n):
        for f in S:
            for r in (0,1):
                tr=T[(f,r)]
                if tr is None: continue
                w,d,t=tr
                if d=='R':
                    rules.append(((q,f),r,(delta[q][w],t),()))
                    if r==0: rules.append(((q,f),BOT,(delta[q][w],t),(BOT,)))
                else:
                    for q2 in range(n):
                        for b in (0,1):
                            if delta[q2][b]!=q: continue
                            rules.append(((q,f),r,(q2,t),(b,w)))
                            if r==0:
                                X=('X',cnt); cnt+=1
                                rules.append(((q,f),BOT,X,(w,BOT)))
                                rules.append((X,w,(q2,t),(b,w)))
    out={}  # state -> set of (a,s)
    def add(s,a,s2):
        st=out.setdefault(s,set())
        if (a,s2) in st: return False
        st.add((a,s2)); return True
    FIN='fin'
    add((0,'A'),BOT,FIN)
    def reach(p,g):
        # states s with p -eps* g-> s
        seen={p}; stack=[p]; res=set()
        while stack:
            x=stack.pop()
            for a,y in out.get(x,()):
                if a is None and y not in seen: seen.add(y); stack.append(y)
                elif a==g: res.add(y)
        return res
    ch=True
    while ch:
        ch=False
        for p,g,p2,push in rules:
            for s in reach(p,g):
                if len(push)==0: ch|=add(p2,None,s)
                elif len(push)==1: ch|=add(p2,push[0],s)
                else:
                    mid=('M',p2,push[0]); ch|=add(p2,push[0],mid); ch|=add(mid,push[1],s)
    for q in range(n):
        for f in S:
            for r in (0,1):
                if T[(f,r)] is None:
                    if reach((q,f),r) or (r==0 and reach((q,f),BOT)): return False
    return True
def dfas(n):
    # delta[q][b]; delta[0][0]=0
    cells=[(q,b) for q in range(n) for b in (0,1) if (q,b)!=(0,0)]
    for vals in itertools.product(range(n),repeat=len(cells)):
        d=[[0,0] for _ in range(n)]
        for (q,b),v in zip(cells,vals): d[q][b]=v
        yield d
def decide(m,N=4):
    T=parse(m)
    for n in range(1,N+1):
        for side,TT in (('L',T),('R',mirror(T))):
            for d in dfas(n):
                if check(TT,n,d): return (side,n,d)
    return None
if __name__=='__main__':
    ms=[l.split(':',1)[1].strip() for l in sys.stdin if l.startswith('UNKNOWN')]
    nd=0
    for m in ms:
        r=decide(m,3)
        print(m,'->',r if r else 'NON DECIDE')
        nd+= r is None
    print(len(ms),'machines,',len(ms)-nd,'prouvees sans arret,',nd,'non decidees')
