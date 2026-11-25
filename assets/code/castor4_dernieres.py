# castor4_dernieres.py : verifie les lemmes des trois preuves a la main pour les machines a 4 etats
# laissees indecises par les criteres automatiques (castors-affaires.html, niveau technologique).
# Affiche : departs 291 8 12 lemmes True
# Une configuration s'ecrit (mot a gauche de la tete, etat, mot a partir de la tete), le reste vide.
def mk(m):
    T={}
    for i,x in enumerate(m.split()):
        T[(i//2,i%2)]=None if x[0]=='-' else (int(x[0]),1 if x[1]=='R' else -1,ord(x[2])-65)
    return T
def conf(left,s,right):
    w=left+right; return {i:int(c) for i,c in enumerate(w) if c=='1'},len(left),'ABCD'.index(s)
def norm(tape,p,s):
    ks=[i for i,v in tape.items() if v]; lo=min(ks+[p]); return frozenset(i-lo for i in ks),p-lo,s
def step(T,tape,p,s):
    tr=T[(s,tape.get(p,0))]
    if tr is None: return None
    tape=dict(tape); tape[p]=tr[0]; return tape,p+tr[1],tr[2]
def runs(T,c,n):
    for _ in range(n):
        c=step(T,*c)
        if c is None: return None
    return c
def lemme(T,a,n,b):
    r=runs(T,conf(*a),n); return r is not None and norm(*r)==norm(*conf(*b))
def atteint(T,c,cible,maxt=10**6):
    cib=norm(*conf(*cible))
    for t in range(1,maxt):
        c=step(T,*c)
        if c is None: return None
        if norm(*c)==cib: return t
    return None
ok=True
# Machine 1 : L(a,b) = 1^a [A] 1 1 (01)^b
M1=mk("1RB 1LD 1RC 0LC 1LA 1RA --- 0RB")
for a in range(2,20):
    for b in range(8): ok&=lemme(M1,('1'*a,'A','11'+'01'*b),4,('1'*(a-2),'A','11'+'01'*(b+1)))
for b in range(8): ok&=lemme(M1,('01','A','11'+'01'*b),4,('','A','01'*(b+2)))
for c in range(8): ok&=lemme(M1,('1'*c,'A','0101'),6,('1'*(c+4),'A',''))
for c in range(8): ok&=lemme(M1,('1'*c,'A',''),3,('1'*(c+1),'A','11'))
d1=atteint(M1,conf('','A',''),('1'*25,'A','11'))
for a in range(1,200,4): ok&= atteint(M1,conf('1'*a,'A','11'),('1'*(a+4),'A','11')) is not None
# Machine 2 : Q(j,m) = 1^j 0 [A] 0 0 1^m
M2=mk("1RB 0RB 1LB 0LC 0LD --- 1RD 0RA")
for j in range(1,15):
    for m in range(8): ok&=lemme(M2,('1'*j+'0','A','00'+'1'*m),5,('1'*(j-1)+'0','A','00'+'1'*(m+1)))
for m in range(8): ok&=lemme(M2,('00','A','00'+'1'*m),8,('1110','A','1'*m))
for k in range(8):
    for m in range(3,12): ok&=lemme(M2,('1'*k+'0','A','1'*m),7,('1'*(k+3)+'0','A','1'*(m-3)))
d2=atteint(M2,conf('','A',''),('1110','A',''))
for k in range(3,200,3): ok&= atteint(M2,conf('1'*k+'0','A',''),('1'*(k+3)+'0','A','')) is not None
# Machine 3 : X(j,m) = 1^j [A] 1 0 1^m
M3=mk("1RB 1LB 1RC 0RD 1LD 1RB --- 0LA")
for j in range(1,15):
    for m in range(8): ok&=lemme(M3,('1'*j,'A','10'+'1'*m),7,('1'*(j-1),'A','10'+'1'*(m+1)))
for m in range(3,12): ok&=lemme(M3,('0','A','10'+'1'*m),7,('1111','A','00'+'1'*(m-3)))
for c in range(10):
    for r in range(3,12): ok&=lemme(M3,('1'*c,'A','00'+'1'*r),5,('1'*(c+3),'A','00'+'1'*(r-3)))
    ok&=lemme(M3,('1'*c,'A','001'),6,('1'*(c+2),'A','101'))
d3=atteint(M3,conf('','A',''),('111','A','101'))
for k in range(3,200,3): ok&= atteint(M3,conf('1'*k,'A','101'),('1'*(k+3),'A','101')) is not None
print('departs',d1,d2,d3,'lemmes',ok)
