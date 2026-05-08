import time
start = time.time()
import matplotlib.pyplot as plt
from numpy import sign, sqrt, tanh, sinh, cosh, pi, arange, zeros, arctan, arcsinh, inf, mean, atanh
from scipy.integrate import quad
from scipy.special import ellipkinc
import numba
import pandas as pd


###Defining Pore Characteristics
#[0, 0, rp] - 2D pore
#[1, Lp, rp] - Cylindrical Pore
#[2, Lp, r1, r2] - Conical Pore, r1 and r2 are bottom and top radii
#[3, Lp, rin, rout] - Hyperbolic Pore

#User-Defined Pore
# pore = [1,3.5,4.45]
pore = [1, 1.1, 1.1]

###Defining Complex Molecules' subunit characteristics
#0 - Cylinder;          block = [0,lc,rc] 
#1 - Sphere;            block = [1,rs]
#2 - Ellipsoid;         block = [2,b,a]
#3 - Wedge;             block = [3,lw,r1,r2,phi]
#4 - Truncated Cone;    block = [4,lco,r1,r2]

#User-Defined Complex Structure
#block = [[0,100,0.99]]
#block = [[0,10,0.25],[1,0.5],[0,10,0.25],[1,0.5],[0,10,0.25]]
#block = [[1,0.5]]
##SpeedBump
#block = [[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1]]
#ShootingStar
#block = [[0,16,sqrt(6)*1.1],[0,300,1.1]]
# block = [[0,16,sqrt(6)*1.1],[0,1033,1.1]]
block = [[0, 0.5, 1.0]]

#Molecule's sub-unit half-lengths and total length
L_rad = [block[i][1] for i in range(len(block))]    
L = 2*sum(L_rad)
Lp = pore[1]

#User-defined resolution
dz = L/20000


###Region-dependent Non-dimensionalization of blocks properties 

##Interior pore region normalization
#Normalization factor (might differ for conical pores)
f_in = pore[2]
bnd_in = [[block[i][j]/f_in for j in range(len(block[i]))] for i in range(len(block))]
for i in range(len(block)):
    bnd_in[i][0] = block[i][0]
    if block[i][0] == 3:    #The angle of the wedged cylinder is normalized by 2pi instead
        bnd_in[i][4] = block[i][4]/2/pi

##Top access region normalization
#Pore-geometry dependent normalization factor
if pore[0] < 2: #2D and cylindrical pores normalized by rp
    f_top = pore[2]
else:           #Conical and Hyperbolic pores normalized by r2 and rout 
    f_top = pore[3]
bnd_top = [[block[i][j]/f_top for j in range(len(block[i]))] for i in range(len(block))]
for i in range(len(block)):
    bnd_top[i][0] = block[i][0]
    if block[i][0] == 3:    #The angle of the wedged cylinder is normalized by 2pi instead
        bnd_top[i][4] = block[i][4]/2/pi
    
##Bottom access region normalization
#Pore-geometry dependent normalization factor
if pore[0] < 2:     #2D and cylindrical pores normalized by rp
    f_bot = pore[2]
elif pore[0] == 2:  #Conical pore normalized by r1 
    f_bot = pore[2]
elif pore[0] == 3:  #Hyperbolic pore normalized by rout 
    f = pore[3]
bnd_bot = [[block[i][j]/f_bot for j in range(len(block[i]))] for i in range(len(block))]
for i in range(len(block)):
    bnd_bot[i][0] = block[i][0]
    if block[i][0] == 3:    #The angle of the wedged cylinder is normalized by 2pi instead
        bnd_bot[i][4] = block[i][4]/2/pi
        

#Numerical values and initialization
zz = arange(-1.25*L-2*Lp,0.25*L+2*Lp+dz,dz) #Array containing distances from pore denter to bottom of molecule
Rbz = zeros(len(zz))    #Array will contain blocked resistance values for each zz normalized by open pore value
dmu = 0.00001           #Resolution for integrals outside the pore / to be removed

###Functions for blocked segments inside pores
##Functions named as Rbin_ij where i is the obstruction type, and j is the pore geometry type
#Cylindrical Pore
def Rbin_01(pore,block,zo,zmin,zmax):  #Cylinder in Cylindrical Pore
    rp = pore[2]
    dc = block[2]
    Y = 2/pi*(zmax/rp - zmin/rp)/(1-dc**2)
    return Y/2/rp
def Rbin_11(pore,block,zo,zmin,zmax):  #Sphere in Cylindrical Pore
    rp = pore[2]
    ds = block[1]
    x1 = zmin/rp
    x2 = zmax/rp
    xo = zo/rp
    Y = 2/pi/sqrt(1-ds**2)*(arctan((x2-xo)/sqrt(1-ds**2))-arctan((x1-xo)/sqrt(1-ds**2)))
    return Y/2/rp
def Rbin_21(pore,block,zo,zmin,zmax):  #Ellipsoid in Cylindrical Pore [2,b/rp,a/rp]
    rp = pore[2]
    xo = zo/rp
    x1 = zmin/rp
    x2 = zmax/rp
    db = block[1]
    da = block[2]
    Y = 2/pi*db/da/sqrt(1-da**2)*(arctan(da/db*(x2-xo)/sqrt(1-da**2))-arctan(da/db*(x1-xo)/sqrt(1-da**2)))
    return Y/2/rp
def Rbin_31(pore,block,zo,zmin,zmax):  #Wedge in Cylindrical Pore [3,lw,r1,r2,phi]
    rp = pore[2]
    d1 = block[2]
    d2 = block[3]
    dp = block[4]
    Y = 2/pi*(zmax/rp-zmin/rp)/(1-(1-dp)*d1**2-dp*d2**2)
    return Y/2/rp
def Rbin_41(pore,block,zo,zmin,zmax):  #Truncated Cone in Cylindrical Pore [4,lco,r1,r2]
    rp = pore[2]
    dL = 2*block[1]
    d1 = block[2]
    d2 = block[3]
    ds = dL/(d2-d1)
    dm = (d1+d2)/2
    Y = 2/pi*ds*(atanh((zmax-zo)/rp/ds+dm)-atanh((zmin-zo)/rp/ds+dm))
    return Y/2/rp

#Conical Pore
def Rbin_02(pore,block,zo,zmin,zmax):  #Cylinder in Conical Pore
    return rc
def Rbin_12(pore,block,zo,zmin,zmax):  #Sphere in Conical Pore
    return rc
def Rbin_22(pore,block,zo,zmin,zmax):  #Ellipsoid in Conical Pore
    return rc
def Rbin_32(pore,block,zo,zmin,zmax):  #Wedge in Conical Pore
    return rc
def Rbin_42(pore,block,zo,zmin,zmax):  #Truncated Cone in Conical Pore
    return rc

#Hyperbolic Pore
def Rbin_03(pore,block,zo,zmin,zmax):  #Cylinder in Hyperbolic Pore
    return rc
def Rbin_13(pore,block,zo,zmin,zmax):  #Sphere in Hyperbolic Pore
    return rc
def Rbin_23(pore,block,zo,zmin,zmax):  #Ellipsoid in Hyperbolic Pore
    return rc
def Rbin_33(pore,block,zo,zmin,zmax):  #Wedge in Hyperbolic Pore
    return rc
def Rbin_43(pore,block,zo,zmin,zmax):  #Truncated Cone in Hyperbolic Pore
    return rc

###Functions for blocked segments outside of pores
##Functions named as Rbout_i where i is the obstruction type
def Rbout_01(pore,block,zo,zmin,zmax):  #Cylinder outside Cylindrical Pore
    rp = pore[2]
    dc = block[2]
    Y = 1/pi*(ellipkinc(pi/2-arctan(zmin/rp),dc**2)-ellipkinc(pi/2-arctan(zmax/rp),dc**2))
    return Y/2/rp
def Rbout_11(pore,block,zo,zmin,zmax):  #Sphere outside Cylindrical Pore [1,rs]
    rp = pore[2]
    Y = quad(f_sphere,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[1],zo/rp))
    return Y[0]/2/rp
def Rbout_21(pore,block,zo,zmin,zmax):  #Ellipsoid outside Cylindrical Pore [2,b,a]
    rp = pore[2]
    Y = quad(f_ellipsoid,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[1],block[2],zo/rp))
    return Y[0]/2/rp
def Rbout_31(pore,block,zo,zmin,zmax):  #Wedge outside Cylindrical Pore [3,lw,r1,r2,phi]
    rp = pore[2]
    Y = quad(f_wedge,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[2],block[3],block[4]))
    return Y[0]/2/rp
def Rbout_41(pore,block,zo,zmin,zmax):  #Truncated Cone outside Cylindrical Pore [4,lco,r1,r2]
    rp = pore[2]
    Y = quad(f_cone,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[1],block[2],block[3],zo/rp))
    return Y[0]/2/rp

#Conical Pore
def Rbout_02(pore,block,zo,zmin,zmax):  #Cylinder outside Conical Pore
    return rc
def Rbout_12(pore,block,zo,zmin,zmax):  #Sphere outside Conical Pore
    return rc
def Rbout_22(pore,block,zo,zmin,zmax):  #Ellipsoid outside Conical Pore
    return rc
def Rbout_32(pore,block,zo,zmin,zmax):  #Wedge outside Conical Pore
    return rc
def Rbout_42(pore,block,zo,zmin,zmax):  #Truncated Cone outside Conical Pore
    return rc

#Hyperbolic Pore
def Rbout_03(pore,block,zo,zmin,zmax):  #Cylinder outside Hyperbolic Pore
    return rc
def Rbout_13(pore,block,zo,zmin,zmax):  #Sphere outside Hyperbolic Pore
    return rc
def Rbout_23(pore,block,zo,zmin,zmax):  #Ellipsoid outside Hyperbolic Pore
    return rc
def Rbout_33(pore,block,zo,zmin,zmax):  #Wedge outside Hyperbolic Pore
    return rc
def Rbout_43(pore,block,zo,zmin,zmax):  #Truncated Cone outside Hyperbolic Pore
    return rc

#Numerically integrated Access region functions 
@numba.njit("f8(f8,f8,f8)", fastmath=True)
def f_sphere(mu,ds,xo):
    den = sqrt(1-(ds**2+xo**2)/(cosh(mu))**2+2*xo**2-2*xo*tanh(mu)*sqrt(1+xo**2-ds**2/(cosh(mu))**2))
    res = 1/pi/den/(cosh(mu))**2
    return res
@numba.njit("f8(f8,f8,f8,f8)", fastmath=True)
def f_wedge(mu,d1,d2,dp):
    den = (1-dp)*sqrt(1-d1**2/(cosh(mu))**2)+dp*sqrt(1-d2**2/(cosh(mu))**2)
    res = 1/pi/den/cosh(mu)
    return res
@numba.njit("f8(f8,f8,f8,f8,f8)", fastmath=True)
def f_cone(mu,dL,d1,d2,xo):
    den = 1-(2*dL/(d2-d1)*(dL*(d2+d1)/(d2-d1)-xo)+sign(mu*(d2-d1))*sqrt(((tanh(mu))**2+4*dL**2/(d2-d1)**2)*(sinh(mu))**2-(tanh(mu))**2*(xo-dL*(d2+d1)/(d2-d1))**2))**2/((cosh(mu))**2*((tanh(mu))**2+4*dL**2/(d2-d1)**2)**2)
    res = 1/pi/sqrt(den)/cosh(mu)
    return res
@numba.njit("f8(f8,f8,f8,f8)", fastmath=True)
def f_ellipsoid(mu,db,da,xo):
    temp = ((tanh(mu))**2-db**2/da**2)*(db**2+xo**2-(sinh(mu))**2)
    den = temp+2*(xo*db/da)**2-sign(mu)*2*xo*db/da*sqrt(temp+(xo*db/da)**2+da**2*((tanh(mu))**2-db**2/da**2)**2)
    den = sqrt(1+den/((tanh(mu))**2-db**2/da**2)**2/(cosh(mu))**2)
    res = 1/pi/den/cosh(mu)
    return res



##Functions for open segments
##Functions for interior segments named as Roin_j where j is the pore geometry type
def Roout_1(pore,zmin,zmax):  #Outside Cylindrical Pore
    rp = pore[2]
    Y = 1/pi*(arctan(zmax/rp)-arctan(zmin/rp))
    return Y/2/rp
def Roout_2(pore,zmin,zmax):  #Outside Conical Pore
    return rc
def Roout_3(pore,zmin,zmax):  #Outside Hyperbolic Pore
    return rc
def Roin_1(pore,zmin,zmax):   #Inside Cylindrical Pore
    rp = pore[2]
    Y = 2/pi*(zmax/rp-zmin/rp)
    return Y/2/rp
def Roin_2(pore,zmin,zmax):   #Inside Conical Pore
    return rc
def Roin_3(pore,zmin,zmax):   #Inside Hyperbolic Pore
    return rc


########

#This loops through z and and through sub-units to determine which function to call 
i=0     #index for z array
for z in zz:
    #Blocked Segment Contribution Calculations
    Rb = 0  #Initializing normalized resistance value
    zo = z+L_rad[0]     #Center of the first sub-unit
    for j in range(len(block)):     #Calculating contribution from each sub-unit

        ###Name of sub-unit specific functions to be called 
        func_name_in = 'Rbin_'+str(block[j][0])+str(pore[0])
        func_name_out = 'Rbout_'+str(block[j][0])+str(pore[0])
        
        #####Testing whether subunit is inside or outside pore, and calling appropriate functions 
        zmin = zo-L_rad[j]
        zmax = zo+L_rad[j]
        if zmax <= -Lp/2:                           #Completely under the pore
            Rb = Rb + locals()[func_name_out](pore,bnd_bot[j],zo+Lp/2,zmin+Lp/2,zmax+Lp/2)
        elif (zmin < -Lp/2) and (abs(zmax) < Lp/2): #Partially inside and under the pore
            Rb = Rb + locals()[func_name_in](pore,bnd_in[j],zo,-Lp/2,zmax)         #Interior contribution
            Rb = Rb + locals()[func_name_out](pore,bnd_bot[j],zo+Lp/2,zmin+Lp/2,0) #Bottom access region contribution
        elif (zmin < -Lp/2) and (zmax > Lp/2):      #Sub-unit longer than pore, spilling above and underneath pore 
            Rb = Rb + locals()[func_name_out](pore,bnd_top[j],zo-Lp/2,0,zmax-Lp/2) #Top access region contribution
            Rb = Rb + locals()[func_name_in](pore,bnd_in[j],zo,-Lp/2,Lp/2)         #Interior contribution
            Rb = Rb + locals()[func_name_out](pore,bnd_bot[j],zo+Lp/2,zmin+Lp/2,0) #Bottom access region contribution
        elif (zmin >= -Lp/2) and (zmax <= Lp/2):    #Sub-unit shorter than pore and completely inside the pore
            Rb = Rb + locals()[func_name_in](pore,bnd_in[j],zo,zmin,zmax)
        elif (abs(zmin) < Lp/2) and (zmax > Lp/2):  #Partially inside and above the pore
            Rb = Rb + locals()[func_name_in](pore,bnd_in[j],zo,zmin,Lp/2)          #Interior contribution
            Rb = Rb + locals()[func_name_out](pore,bnd_top[j],zo-Lp/2,0,zmax-Lp/2) #Top access region contribution
        if zmin >= Lp/2:                            #Completely above the pore
            Rb = Rb + locals()[func_name_out](pore,bnd_top[j],zo-Lp/2,zmin-Lp/2,zmax-Lp/2)


        if j != len(block):     #Centering zo around the next unit
            zo = zo + sum(L_rad[j:j+2])

    #Open Segment Contribution Calculations
    zmax = z + L
    ###Name of region-specific functions to be called 
    func_name_in = 'Roin_'+str(pore[0])
    func_name_out = 'Roout_'+str(pore[0])

    ##Testing whether molecule is inside or outside pore, and calling appropriate functions 
    if zmax <= -Lp/2:                           #Molecule completely under pore
        Rb = Rb + locals()[func_name_out](pore,0,inf)           #Empty Top Access Region
        Rb = Rb + locals()[func_name_in](pore,-Lp/2,Lp/2)       #Empty Pore
        Rb = Rb + locals()[func_name_out](pore,zmax+Lp/2,0)     #Bottom access region, above molecule
        Rb = Rb + locals()[func_name_out](pore,-inf,z+Lp/2)     #Bottom access region, under Molecule
    elif (z < -Lp/2) and (abs(zmax) < Lp/2):    #Moelcule partially inside and under the pore
        Rb = Rb + locals()[func_name_out](pore,0,inf)           #Empty top access region
        Rb = Rb + locals()[func_name_in](pore,zmax,Lp/2)        #Inside Pore, above molecule
        Rb = Rb + locals()[func_name_out](pore,-inf,z+Lp/2)     #Bottom access region, under Molecule
    elif (z > -Lp/2) and (zmax < Lp/2):         #Molecule shorter and completely inside the pore
        Rb = Rb + locals()[func_name_out](pore,0,inf)           #Empty top access region
        Rb = Rb + locals()[func_name_in](pore,zmax,Lp/2)        #Inside Pore, above molecule
        Rb = Rb + locals()[func_name_in](pore,-Lp/2,z)          #Inside Pore, under molecule
        Rb = Rb + locals()[func_name_out](pore,-inf,-0)         #Empty bottom access region
    elif (z < -Lp/2) and (zmax > Lp/2):         #Molecule longer than pore, spilling above and underneath pore 
        Rb = Rb + locals()[func_name_out](pore,zmax-Lp/2,inf)   #Above Molecule
        Rb = Rb + locals()[func_name_out](pore,-inf,z+Lp/2)     #Under Molecule
    elif (abs(z) < Lp/2) and (zmax > Lp/2):     #Molecule partially inside and above the pore
        Rb = Rb + locals()[func_name_out](pore,zmax-Lp/2,inf)   #Top access region, above Molecule
        Rb = Rb + locals()[func_name_in](pore,-Lp/2,z)          #Inside Pore, under molecule
        Rb = Rb + locals()[func_name_out](pore,-inf,-0)         #Empty bottom access region 
    if z > Lp/2:                                #Molecule completely above pore
        Rb = Rb + locals()[func_name_out](pore,zmax-Lp/2,inf)   #Top access region, Above Molecule
        Rb = Rb + locals()[func_name_out](pore,0,z-Lp/2)        #Top access region, Under Molecule
        Rb = Rb + locals()[func_name_in](pore,-Lp/2,Lp/2)       #Empty Pore
        Rb = Rb + locals()[func_name_out](pore,-inf,-0)         #Empty bottom access region

    ##Updating resistance before loop end
    Rbz[i] = Rb
    i = i+1

#Normalizing by open pore resistance
Racc = locals()['Roout_'+str(pore[0])](pore,0,inf) + locals()['Roout_'+str(pore[0])](pore,-inf,-0)
Rpore = locals()['Roin_'+str(pore[0])](pore,-Lp/2,Lp/2)
Ropen = Racc+Rpore
GbGo = (Rbz/Ropen)**-1

plt.plot(zz-mean(zz),GbGo)
plt.show()