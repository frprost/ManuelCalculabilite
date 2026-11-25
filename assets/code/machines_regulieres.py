# Machines de Turing régulières (méthode du polycopié de Ch. Boitet), construites et testées.
# Compagnon de la page equivalence.html#machines-regulieres du manuel de calculabilité.
# Sémantique des quadruplets : (état, symbole lu) -> (action, nouvel état), action = 'L', 'R' ou symbole écrit.
# Convention des macros "E" : bande = blocs de barres séparés par UN blanc ; tête en E (deux cases après la dernière barre).
import itertools, sys
B,BAR,XM='B','1','X'
CNT=[0]
MAXD=[8]
Z3SYMS=('B','1','X')
def fresh(p='s'):
    CNT[0]+=1; return '%s%d'%(p,CNT[0])
class M:
    def __init__(s,q,start,finals):
        s.q=q; s.start=start; s.finals=finals   # finals : dict nom -> état
    def syms(s):
        r={B,BAR}
        for (a,x),(act,n) in s.q.items():
            r.add(x)
            if act not in ('L','R'): r.add(act)
        return r
    def states(s):
        r={s.start}|set(s.finals.values())
        for (a,x),(act,n) in s.q.items(): r.add(a); r.add(n)
        return r
def merge(*ms):
    q={}
    for m in ms:
        for k,v in m.q.items():
            assert k not in q, k
            q[k]=v
    return q
def link(q,a,b,syms):
    for x in (B,BAR,XM):
        assert (a,x) not in q,(a,x)
        q[(a,x)]=(x,b)
def seq(*ms):
    syms=set().union(*[m.syms() for m in ms])|{XM}
    q=merge(*ms)
    for m1,m2 in zip(ms,ms[1:]):
        link(q,m1.finals['f'],m2.start,syms)
    return M(q,ms[0].start,{'f':ms[-1].finals['f']})
def mk(spec,finals=('f',)):
    """spec : liste de (état, symbole, action, état) avec noms locaux ; 'e' = départ."""
    ren={}
    def r(n):
        if n not in ren: ren[n]=fresh(n)
        return ren[n]
    q={}
    for a,x,act,n in spec:
        assert (r(a),x) not in q
        q[(r(a),x)]=(act,r(n))
    return M(q,r('e'),{f:r(f) for f in finals})
# --- macros convention E
def goE_spec(a,out):  # depuis une case du contenu (barre ou blanc séparateur), aller en E
    return [(a,BAR,'R',a),(a,B,'R',a+'_b'),(a+'_b',BAR,'R',a),(a+'_b',B,B,out)]
def CopyFromEnd(j):
    sp=[('e',B,'L','c0')]
    cur='c0'
    for t in range(1,j+1):
        l='l%d'%t
        sp.append((cur,B,'L',l)); sp.append((l,BAR,'L',l))
        if t<j: sp.append((l,B,B,'c%d'%t)); cur='c%d'%t
        else: sp.append((l,B,'R','s'))
    sp+=[('s',BAR,XM,'a1'),('a1',XM,'R','a1'),('a1',BAR,'R','a1'),('a1',B,'R','a2'),('a2',BAR,'R','a1'),('a2',XM,'R','a1'),('a2',B,BAR,'r'),
         ('r',BAR,'L','r'),('r',B,'L','r'),('r',XM,BAR,'n1'),('n1',BAR,'R','n2'),('n2',BAR,XM,'b1'),
         ('b1',XM,'R','b1'),('b1',BAR,'R','b1'),('b1',B,'R','b2'),('b2',BAR,'R','b1'),('b2',XM,'R','b1'),('b2',B,'L','b3'),('b3',B,BAR,'r'),
         ('n2',B,B,'g')]
    sp+=goE_spec('g','f')
    return mk(sp)
def IncLast(): return mk([('e',B,'L','t'),('t',B,BAR,'u'),('u',BAR,'R','v'),('v',B,'R','f')])
def DecLast(): return mk([('e',B,'L','a'),('a',B,'L','b'),('b',BAR,B,'c'),('c',B,'R','f')])
def AppendZero(): return mk([('e',B,BAR,'a'),('a',BAR,'R','b'),('b',B,'R','f')])
def EraseLast(): return mk([('e',B,'L','a'),('a',B,'L','b'),('b',BAR,B,'c'),('c',B,'L','b'),('b',B,'R','f')])
def TestZero(j):
    sp=[('e',B,'L','c0')]; cur='c0'
    for t in range(1,j+1):
        l='l%d'%t
        sp.append((cur,B,'L',l)); sp.append((l,BAR,'L',l))
        if t<j: sp.append((l,B,B,'c%d'%t)); cur='c%d'%t
        else: sp.append((l,B,'R','s'))
    sp+=[('s',BAR,'R','a'),('a',B,B,'y0'),('a',BAR,BAR,'n0')]
    sp+=goE_spec('y0','yes')+goE_spec('n0','no')
    return mk(sp,finals=('yes','no'))
def KeepLast():
    sp=[('e',B,'L','a'),('a',B,'L','b'),('b',BAR,'L','b'),('b',B,'L','k'),
        ('k',BAR,B,'kk'),('kk',B,'L','k'),('k',B,'L','k2'),('k2',BAR,B,'kk'),('k2',B,'R','g0'),
        ('g0',B,'R','g0b'),('g0b',B,'R','g1')]
    # g1 : on avance vers le dernier bloc (blancs puis barres)
    sp+=[('g1',B,'R','g1'),('g1',BAR,BAR,'h')]
    sp+=goE_spec('h','f')
    return mk(sp)
def GoLeft():  # de E à la barre la plus à gauche
    return mk([('e',B,'L','v'),('v',B,'L','w'),('w',BAR,'L','w'),('w',B,'L','x'),('x',BAR,'L','w'),('x',B,'R','y'),('y',B,'R','f')])
# --- normalisation : N(Z, m, d) remplace les m derniers blocs par le bloc de Psi_Z(arguments)
def N(Z,m,d):
    lam,rho='λ%d'%d,'ρ%d'%d
    t=fresh('N')
    zs=lambda s: t+'|'+s
    q={}
    def add(a,x,act,n):
        assert (a,x) not in q,(a,x); q[(a,x)]=(act,n)
    L=lambda n: t+n
    S=Z.syms()|{B,BAR}
    # Z1 : poser ρ en E-1, remonter m blocs, poser λ, aller sur la première barre
    add(L('e'),B,'L',L('a')); add(L('a'),B,rho,L('a')); add(L('a'),rho,'L',L('b1'))
    for k in range(1,m+1):
        add(L('b%d'%k),BAR,'L',L('b%d'%k))
        if k<m: add(L('b%d'%k),B,'L',L('b%d'%(k+1)))
        else: add(L('b%d'%k),B,lam,L('c')); add(L('c'),lam,'R',zs(Z.start))
    # Z2
    for (a,x),(act,n) in Z.q.items(): add(zs(a),x,act,zs(n))
    FL=['λ%d'%e for e in range(d+1,MAXD[0]+1)]; FR=['ρ%d'%e for e in range(d+1,MAXD[0]+1)]
    Ltg={n for (a,x),(act,n) in Z.q.items() if act=='L'}; Rtg={n for (a,x),(act,n) in Z.q.items() if act=='R'}
    for a in Z.states():
        A=zs(a); u=lambda x: A+'~'+t+x
        # ρ : insérer un blanc à la place de ρ, en repoussant ρ et les bornes extérieures
        if a in Rtg and (zs(a),rho) not in q:
            add(A,rho,B,u('r1')); add(u('r1'),B,'R',u('P'+rho))
            for c in [rho]+FR:
                add(u('P'+c),B,c,u('K'))
                for f in FR: add(u('P'+c),f,c,u('W'+f))
            for f in FR:
                for c in [rho]+FR: add(u('W'+f),c,'R',u('P'+f))
            for c in FR: add(u('K'),c,'L',u('K'))
            add(u('K'),rho,'L',u('r3')); add(u('r3'),B,B,A)
        # λ : décaler d'une case à gauche tout ce qui est à gauche de λ (jusqu'au premier double blanc)
        if a in Ltg and (zs(a),lam) not in q:
            add(A,lam,lam,u('g')); add(u('g'),lam,'L',u('g1'))
            for c in [BAR]+FL: add(u('g1'),c,'L',u('g1')); add(u('g2'),c,'L',u('g1'))
            add(u('g1'),B,'L',u('g2')); add(u('g2'),B,'R',u('g3')); add(u('g3'),B,'R',u('s'))
            for c in [BAR]+FL:
                add(u('s'),c,B,u('s1'+c)); add(u('s1'+c),B,'L',u('s2'+c)); add(u('s2'+c),B,c,u('s3')); add(u('s3'),c,'R',u('s4'))
            add(u('s4'),B,'R',u('s')); add(u('s'),B,'R',u('s'))
            add(u('s'),lam,B,u('t1')); add(u('t1'),B,'L',u('t2')); add(u('t2'),B,lam,u('t3')); add(u('t3'),lam,'R',u('t4')); add(u('t4'),B,B,A)
    # Z3 : couples terminaux -> qL
    qL=L('qL')
    for a in Z.states():
        for x in Z3SYMS:
            if (a,x) not in Z.q: add(zs(a),x,x,qL)
    # Z4 : regrouper les barres juste à droite de λ, ajouter une barre, effacer λ et ρ, aller en E
    ALL=S|{lam,rho}
    for x in ALL-{lam}: add(qL,x,'L',qL)
    add(qL,lam,'R',L('A'))
    nb=ALL-{BAR,rho,lam}
    add(L('A'),BAR,'R',L('A')); add(L('A'),rho,rho,L('C'))
    for x in nb: add(L('A'),x,x,L('F'))
    for x in nb: add(L('F'),x,'R',L('F'))
    add(L('F'),BAR,B,L('G')); add(L('F'),rho,rho,L('C'))
    for x in nb: add(L('G'),x,'L',L('G'))
    add(L('G'),BAR,'R',L('H')); add(L('G'),lam,'R',L('H'))
    for x in nb: add(L('H'),x,BAR,L('A'))
    add(L('C'),rho,B,L('C2'))
    add(L('C2'),B,'L',L('C2'))
    for x in nb-{B}: add(L('C2'),x,B,L('C2'))
    add(L('C2'),BAR,'R',L('C5')); add(L('C2'),lam,'R',L('C5'))
    add(L('C5'),B,BAR,L('C6')); add(L('C6'),BAR,'L',L('C6')); add(L('C6'),lam,B,L('C7'))
    add(L('C7'),B,'R',L('C8')); add(L('C8'),BAR,'R',L('C8')); add(L('C8'),B,'R',L('C9')); add(L('C9'),BAR,'R',L('C8')); add(L('C9'),B,B,L('f'))
    return M(q,L('e'),{'f':L('f')}),d
# --- fonctions -> machines autonomes (convention Boitet : départ sur la première barre, résultat = nombre de barres)
class Fn:
    def __init__(s,arity,pyf,build,depth): s.n=arity; s.py=pyf; s.build=build; s.depth=depth
def standalone(asm):
    # depuis la première barre de l'entrée : aller en E, assembler, garder le dernier bloc, retirer une barre
    g=mk(goE_spec('e','f'))
    return seq(g,asm,KeepLast(),DecLast())
def Nf(f,m):  # normalisée de la machine autonome de f
    Z=f.build()
    mach,_=N(Z,m,f.depth+1)
    return mach
def Proj(n,i): return Fn(n,lambda *x:x[i-1],lambda: standalone(seq(*[CopyFromEnd(n-i+1)])),0)
def Const(n,c): return Fn(n,lambda *x:c,lambda: standalone(seq(AppendZero(),*[IncLast() for _ in range(c)])),0)
Succ=Fn(1,lambda x:x+1,lambda: mk([('e',BAR,BAR,'f')]),0)   # machine vide (q0 sur x+1 barres)
def Comp(g,hs):
    n=hs[0].n; k=len(hs)
    def build():
        parts=[]
        for i,h in enumerate(hs,1):
            parts+=[CopyFromEnd(n+i-1) for _ in range(n)]+[Nf(h,n)]
        parts+=[CopyFromEnd(k) for _ in range(k)]+[Nf(g,k)]
        return standalone(seq(*parts))
    return Fn(n,lambda *x:g.py(*[h.py(*x) for h in hs]),build,max([g.depth]+[h.depth for h in hs])+1)
def Mu(g):
    n=g.n-1
    def build():
        start=AppendZero()
        body=seq(*([CopyFromEnd(n+1) for _ in range(n+1)]+[Nf(g,n+1)]))
        tz=TestZero(1)
        yes=seq(EraseLast(),KeepLast())
        no=seq(EraseLast(),IncLast())
        syms=set().union(start.syms(),body.syms(),tz.syms(),yes.syms(),no.syms())|{XM}
        q=merge(start,body,tz,yes,no)
        link(q,start.finals['f'],body.start,syms)
        link(q,body.finals['f'],tz.start,syms)
        link(q,tz.finals['yes'],yes.start,syms)
        link(q,tz.finals['no'],no.start,syms)
        link(q,no.finals['f'],body.start,syms)
        asm=M(q,start.start,{'f':yes.finals['f']})
        return standalone(asm)
    def py(*x):
        y=0
        while g.py(*x,y)!=0: y+=1
        return y
    return Fn(n,py,build,g.depth+1)
def Rec(g,h,n,const=None):
    # f(x,0)=g(x), f(x,y+1)=h(x,y,f(x,y)) ; n = nombre de paramètres (g d'arité n, ou constante si n=0)
    def build():
        init=[AppendZero()]
        if n==0: init+=[AppendZero()]+[IncLast() for _ in range(const)]
        else: init+=[CopyFromEnd(n+2) for _ in range(n)]+[Nf(g,n)]
        init=seq(*init)
        tz=TestZero(3)
        step=[CopyFromEnd(n+3) for _ in range(n)]+[CopyFromEnd(n+2),CopyFromEnd(n+2),Nf(h,n+2)]
        step+=[CopyFromEnd(n+4) for _ in range(n)]+[CopyFromEnd(n+4),DecLast(),CopyFromEnd(n+4),IncLast(),CopyFromEnd(n+3)]
        step=seq(*step)
        yes=KeepLast()
        syms=set().union(init.syms(),tz.syms(),step.syms(),yes.syms())|{XM}
        q=merge(init,tz,step,yes)
        link(q,init.finals['f'],tz.start,syms)
        link(q,tz.finals['yes'],yes.start,syms)
        link(q,tz.finals['no'],step.start,syms)
        link(q,step.finals['f'],tz.start,syms)
        return standalone(M(q,init.start,{'f':yes.finals['f']}))
    def py(*a):
        *x,y=a
        v=const if n==0 else g.py(*x)
        for i in range(y): v=h.py(*x,i,v)
        return v
    return Fn(n+1,py,build,max(g.depth if g else 0,h.depth)+1)
# --- exécution
def run(m,tape_list,maxsteps=5*10**7):
    tape={i:c for i,c in enumerate(tape_list) if c!=B}
    h=0; st=m.start; n=0; q=m.q
    while True:
        k=(st,tape.get(h,B))
        if k not in q: break
        a,nx=q[k]
        if a=='L': h-=1
        elif a=='R': h+=1
        elif a==B: tape.pop(h,None)
        else: tape[h]=a
        st=nx; n+=1
        if n>maxsteps: return None
    return st,h,tape,n
def enc(xs):
    t=[]
    for i,x in enumerate(xs):
        if i: t.append(B)
        t+=[BAR]*(x+1)
    return t
def psi(f,args):
    m=f.build(); r=run(m,enc(args))
    if r is None: return None
    st,h,tape,n=r
    return sum(1 for v in tape.values() if v==BAR), n, len(m.q)

# =====================================================================
# Tests.  python3 machines_regulieres.py        (quelques minutes)
#         python3 machines_regulieres.py long   (ajoute multiplication et minimisation : ~30 min, plusieurs Go)
# =====================================================================
import itertools

def raw(spec,n):
    q={(a,x):(act,b) for a,x,act,b in spec}
    m=M(q,'q0',{})
    def py(*args):
        r=run(m,enc(args)); return sum(1 for v in r[2].values() if v==BAR)
    return Fn(n,py,lambda:m,0)
Za=raw([('q0','1','L','q1'),('q1','B','L','q2'),('q2','B','1','q3'),('q3','1','R','q4'),('q4','B','R','q5'),('q5','1','R','q5'),('q5','B','R','q6'),('q6','B','X','q7'),('q7','X','R','q8'),('q8','B','1','q9')],1)
Zb=raw([('q0','1','L','q1'),('q1','B','1','q2'),('q2','1','L','q3'),('q3','B','1','q4'),('q4','1','L','q5'),('q5','B','X','q6')],1)
# Zc : 2 arguments ; efface le séparateur et va écrire une barre loin à gauche puis loin à droite
Zc=raw([('q0','1','R','q0'),('q0','B','X','q1'),('q1','X','R','q2'),('q2','1','R','q2'),('q2','B','R','q3'),('q3','B','R','q4'),('q4','B','1','q5'),('q5','1','L','q5'),('q5','B','L','q5'),('q5','X','L','q6'),('q6','1','L','q6'),('q6','B','L','q7'),('q7','B','L','q8'),('q8','B','1','q9')],2)

def bars(t): return sum(1 for v in t.values() if v==BAR)
def T(name,f,rng):
    MAXD[0]=f.depth+1
    m=f.build(); ok=True; mx=0
    for args in rng:
        r=run(m,enc(args)); got=None if r is None else bars(r[2])
        if got!=f.py(*args): ok=False; print('  ÉCHEC',name,args,got,f.py(*args)); break
        mx=max(mx,r[3])
    print('%-28s %-5s %9d quadruplets, %7d pas au plus'%(name,ok,len(m.q),mx),flush=True)
def check_reg(name,m,f,rng):
    ok=True
    for args in rng:
        st,h,tape,_=run(m,enc(args)); lo=min(tape)
        cells=[tape.get(i,B) for i in range(lo,max(tape)+1)]
        if not(st==m.finals['f'] and h==lo and cells==enc([f(*args)]) and not any((st,x) in m.q for x in (B,BAR,XM))):
            ok=False; print('  ÉCHEC',name,args); break
    print('%-28s régulière : %s'%(name,ok),flush=True)
if __name__=='__main__':
    import sys
    add=Rec(Proj(1,1),Comp(Succ,[Proj(3,3)]),1)
    pd=Rec(None,Proj(2,1),0,const=0)
    monus=Rec(Proj(1,1),Comp(pd,[Proj(3,3)]),1)
    T('projection A(3,2)',Proj(3,2),itertools.product(range(3),repeat=3))
    T('constante 3',Const(2,3),itertools.product(range(3),repeat=2))
    T('addition',add,itertools.product(range(4),repeat=2))
    T('prédécesseur',pd,[(x,) for x in range(5)])
    T('soustraction bornée',monus,itertools.product(range(4),repeat=2))
    T('Za o A(2,2)',Comp(Za,[Proj(2,2)]),itertools.product(range(3),repeat=2))
    T('Zb o A(3,1)',Comp(Zb,[Proj(3,1)]),itertools.product(range(2),repeat=3))
    T('Zc(A(2,2),A(2,1))',Comp(Zc,[Proj(2,2),Proj(2,1)]),itertools.product(range(3),repeat=2))
    T('Zb(Za(x))',Comp(Zb,[Comp(Za,[Proj(2,1)])]),itertools.product(range(3),repeat=2))
    T('Zc(Zb(x),Za(x))',Comp(Zc,[Comp(Zb,[Proj(1,1)]),Comp(Za,[Proj(1,1)])]),[(x,) for x in range(4)])
    T('récursion, h = Zc',Rec(Proj(1,1),Comp(Zc,[Proj(3,3),Proj(3,2)]),1),itertools.product(range(3),repeat=2))
    for nm,Z in (('Za',Za),('Zb',Zb),('Zc',Zc)):
        MAXD[0]=1
        check_reg("Z' pour "+nm,seq(mk(goE_spec('e','f')),N(Z.build(),Z.n,1)[0],GoLeft()),Z.py,itertools.product(range(4),repeat=Z.n))
    for nm,f,rng in (('addition',add,itertools.product(range(3),repeat=2)),('Zc(Zb(x),Za(x))',Comp(Zc,[Comp(Zb,[Proj(1,1)]),Comp(Za,[Proj(1,1)])]),[(x,) for x in range(3)])):
        MAXD[0]=f.depth+1
        check_reg(nm,seq(f.build(),IncLast(),GoLeft()),f.py,rng)
    if 'long' in sys.argv:
        T('multiplication',Rec(Const(1,0),Comp(add,[Proj(3,3),Proj(3,1)]),1),itertools.product(range(3),repeat=2))
        T('minimisation mu y [x-y=0]',Mu(Comp(monus,[Proj(2,1),Proj(2,2)])),[(x,) for x in range(4)])
