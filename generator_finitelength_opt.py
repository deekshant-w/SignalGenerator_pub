import time
start = time.time()
import matplotlib.pyplot as plt
from numpy import sign, sqrt, tanh, sinh, cosh, pi, linspace, zeros, arctan, arcsinh, inf, mean, arctanh, log
atanh = arctanh
from scipy.integrate import quad
from scipy.special import ellipkinc
import numba

###Functions returning z-dependent radius of conical and hyperbolic pores
def rp_con(pore,z):   #Conical Pore 
    L = pore[1]
    r1 = pore[2]
    r2 = pore[3]
    return 0.5*(r1+r2)+(r2-r1)/L*z

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
    dLp = pore[1]/pore[2]
    dr = pore[3]/pore[2]
    dpmin = rp_con(pore,zmin)/pore[2]
    dpmax = rp_con(pore,zmax)/pore[2]
    dc = block[2]
    Y = -1/pi*dLp/(dr-1)/dc*log((1+dpmax/dc)*(1-dpmin/dc)/(1+dpmin/dc)/(1-dpmax/dc))
    return Y/2/pore[2]
def Rbin_12(pore,block,zo,zmin,zmax):  #Sphere in Conical Pore
    dr = pore[3]/pore[2]
    m = (pore[3]-pore[2])/pore[1]
    drm = (dr+1)/2
    ds = block[1]
    xo = zo/pore[2]
    x1 = zmin/pore[2]
    x2 = zmax/pore[2]
    M = (m**2+1)
    D = (drm*m-xo)
    x_lim = (ds*sqrt(1+m**2)-drm)/m
    if (xo*m > x_lim*m):
        C = sqrt((xo*m+drm)**2-(1+m**2)*ds**2)
        Y = 2/pi/C*(arctan((M*x2+D)/C)-arctan((M*x1+D)/C))
    else:
        C = sqrt((1+m**2)*ds**2-(xo*m+drm)**2)
        Y = 1/pi/C*(log((M*x2+D-C)/(M*x2+D+C))-log((M*x1+D-C)/(M*x1+D+C)))
    return Y/2/pore[2]
def Rbin_22(pore,block,zo,zmin,zmax):  #Ellipsoid in Conical Pore [2,b/rp,a/rp]
    dr = pore[3]/pore[2]
    m = (pore[3]-pore[2])/pore[1]
    drm = (dr+1)/2
    db = block[1]
    da = block[2]
    xo = zo/pore[2]
    x1 = zmin/pore[2]
    x2 = zmax/pore[2]
    M = (m**2+da**2/db**2)
    D = (drm*m-da**2/db**2*xo)
    x_lim = (sqrt(da**2+db**2*m**2)-drm)/m
    if (xo*m > x_lim*m):
        C = sqrt((da/db)**2*(xo*m+drm)**2-da**2*((da/db)**2+m**2))
        Y = 2/pi/C*(arctan((M*x2+D)/C)-arctan((M*x1+D)/C))
    else:
        C = sqrt(-(da/db)**2*(xo*m+drm)**2+da**2*((da/db)**2+m**2))
        Y = 1/pi/C*(log((M*x2+D-C)/(M*x2+D+C))-log((M*x1+D-C)/(M*x1+D+C)))
    return Y/2/pore[2]

def Rbin_32(pore,block,zo,zmin,zmax):  #Wedge in Conical Pore, block=[3,lw/rp1,r1/rp1,r2/rp1,phi/2/pi]
    dL = pore[1]/pore[2]
    dr = pore[3]/pore[2]
    dpmin = rp_con(pore,zmin)
    dpmax = rp_con(pore,zmax)
    dp = block[4]
    d1 = block[2]
    d2 = block[3]
    den = sqrt(dp*d2**2+(1-dp)*d1**2)
    Y = 2/pi*dL/(dr-1)/den*(atanh(dpmin/den)-atanh(dpmax/den))
    return Y/2/pore[2]

def Rbin_42(pore,block,zo,zmin,zmax):  #Truncated Cone in Conical Pore block=[4,lco/rp1,c1/rp1,c2/rp1]
    dr = pore[3]/pore[2]
    m = (pore[3]-pore[2])/pore[1]
    drm = (dr+1)/2
    mc = (block[3]-block[2])/2/block[1]
    drc = (block[3]+block[2])/2
    xo = zo/pore[2]
    x1 = zmin/pore[2]
    x2 = zmax/pore[2]
    M = m**2-mc**2
    D = drm*m-drc*mc+mc**2*xo
    C = m*mc*xo+drm*mc-drc*m
    Y = 1/pi/C*(log(abs((M*x2+D-C)/(M*x2+D+C)))-log(abs((M*x1+D-C)/(M*x1+D+C))))
    return Y/2/pore[2]

#Hyperbolic Pore
def Rbin_03(pore,block,zo,zmin,zmax):  #Cylinder in Hyperbolic Pore, block=[0,lc/rin,rc/rin]
    dL = pore[1]/pore[2]
    dr = pore[3]/pore[2]
    x1 = zmin/pore[2]
    x2 = zmax/pore[2]
    dc = block[2]
    Y = 1/pi*dL/sqrt((1-dc**2)*(dr**2-1))*(arctan(2/dL*sqrt((dr**2-1)/(1-dc**2))*x2)-arctan(2/dL*sqrt((dr**2-1)/(1-dc**2))*x1))
    return Y/2/pore[2]
def Rbin_13(pore,block,zo,zmin,zmax):  #Sphere in Hyperbolic Pore, block=[1,rs/rin]
    dL = pore[1]/pore[2]
    dr = pore[3]/pore[2]
    xo = zo/pore[2]
    x1 = zmin/pore[2]
    x2 = zmax/pore[2]
    ds = block[1]
    da = 4*(dr**2-1)/dL**2 + 1
    db = -2*xo
    dc = 1-ds**2+xo**2
    Y = 4/pi/sqrt(4*da*dc-db**2)*(arctan((2*da*x2+db)/sqrt(4*da*dc-db**2)) - arctan((2*da*x1+db)/sqrt(4*da*dc-db**2)))
    return Y/2/pore[2]
def Rbin_23(pore,block,zo,zmin,zmax):  #Ellipsoid in Hyperbolic Pore, block=[2,b/rin,a/rin]
    dL = pore[1]/pore[2]
    dr = pore[3]/pore[2]
    da = block[2]
    db = block[1]
    xo = zo/pore[2]
    x1 = zmin/pore[2]
    x2 = zmax/pore[2]
    ds = block[1]
    dA = 4*(dr**2-1)/dL**2 + da**2/db**2
    dB = -2*da**2/db**2*xo
    dC = 1-da**2+da**2/db**2*xo**2
    Y = 4/pi/sqrt(4*dA*dC-dB**2)*(arctan((2*dA*x2+dB)/sqrt(4*dA*dC-dB**2)) - arctan((2*dA*x1+dB)/sqrt(4*dA*dC-dB**2)))
    return Y/2/pore[2]
def Rbin_33(pore,block,zo,zmin,zmax):  #Wedge in Hyperbolic Pore, block=[3,lw/rin,r1/rin,r2/rin,phi/2/pi]
    dL = pore[1]/pore[2]
    dr = pore[3]/pore[2]
    d1 = block[2]
    d2 = block[3]
    dp = block[4]
    x1 = zmin/pore[2]
    x2 = zmax/pore[2]
    den = sqrt((1-dp*d2**2-(1-dp)*d1**2)*(dr**2-1))
    Y = 1/pi*dL/den*(arctan(2/dL*sqrt(dr**2-1)/den*x2)-arctan(2/dL*sqrt(dr**2-1)/den*x1))
    return Y/2/pore[2]
def Rbin_43(pore,block,zo,zmin,zmax):  #Truncated Cone in Hyperbolic Pore, block=[4,lco/rin,r1/rin,r2/rin]
    dLp = pore[1]/pore[2]
    dr = pore[3]/pore[2]
    dLc = 2*block[1]/pore[2]
    xo = zo/pore[2]
    x1 = zmin/pore[2]
    x2 = zmax/pore[2]
    d1 = block[2]
    d2 = block[3]
    da = 4*(dr**2-1)/dLp**2 - (d2-d1)**2/dLc**2
    db = -2*(d2-d1)**2/dLc**2*xo-(d2**2-d1**2)/dLc
    dc = 1-(d2-d1)**2/dLc**2*xo**2+(d2**2-d1**2)/dLc*xo-0.25*(d1+d2)**2
    Y = 4/pi/sqrt(4*da*dc-db**2)*(arctan((2*da*x2+db)/sqrt(4*da*dc-db**2)) - arctan((2*da*x1+db)/sqrt(4*da*dc-db**2)))
    return Y/2/pore[2]

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
    if zmin < 0:        #Bottom acces region contribution
        rp = pore[2]
    elif zmax > 0:      #Top access region contribution
        rp = pore[3]
    dc = block[2]
    Y = 1/pi*(ellipkinc(pi/2-arctan(zmin/rp),dc**2)-ellipkinc(pi/2-arctan(zmax/rp),dc**2))
    return Y/2/rp
def Rbout_12(pore,block,zo,zmin,zmax):  #Sphere outside Conical Pore
    if zmin < 0:        #Bottom acces region contribution
        rp = pore[2]
    elif zmax > 0:      #Top access region contribution
        rp = pore[3]
    Y = quad(f_sphere,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[1],zo/rp))
    return Y[0]/2/rp
def Rbout_22(pore,block,zo,zmin,zmax):  #Ellipsoid outside Conical Pore
    if zmin < 0:        #Bottom acces region contribution
        rp = pore[2]
    elif zmax > 0:      #Top access region contribution
        rp = pore[3]
    Y = quad(f_ellipsoid,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[1],block[2],zo/rp))
    return Y[0]/2/rp
def Rbout_32(pore,block,zo,zmin,zmax):  #Wedge outside Conical Pore
    if zmin < 0:        #Bottom acces region contribution
        rp = pore[2]
    elif zmax > 0:      #Top access region contribution
        rp = pore[3]
    Y = quad(f_wedge,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[2],block[3],block[4]))
    return Y[0]/2/rp
def Rbout_42(pore,block,zo,zmin,zmax):  #Truncated Cone outside Conical Pore
    if zmin < 0:        #Bottom acces region contribution
        rp = pore[2]
    elif zmax > 0:      #Top access region contribution
        rp = pore[3]
    Y = quad(f_cone,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[1],block[2],block[3],zo/rp))
    return Y[0]/2/rp

#Hyperbolic Pore
def Rbout_03(pore,block,zo,zmin,zmax):  #Cylinder outside Hyperbolic Pore
    rp = pore[3]
    dc = block[2]
    Y = 1/pi*(ellipkinc(pi/2-arctan(zmin/rp),dc**2)-ellipkinc(pi/2-arctan(zmax/rp),dc**2))
    return Y/2/rp
def Rbout_13(pore,block,zo,zmin,zmax):  #Sphere outside Hyperbolic Pore
    rp = pore[3]
    Y = quad(f_sphere,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[1],zo/rp))
    return Y[0]/2/rp
def Rbout_23(pore,block,zo,zmin,zmax):  #Ellipsoid outside Hyperbolic Pore
    rp = pore[3]
    Y = quad(f_ellipsoid,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[1],block[2],zo/rp))
    return Y[0]/2/rp
def Rbout_33(pore,block,zo,zmin,zmax):  #Wedge outside Hyperbolic Pore
    rp = pore[3]
    Y = quad(f_wedge,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[2],block[3],block[4]))
    return Y[0]/2/rp
def Rbout_43(pore,block,zo,zmin,zmax):  #Truncated Cone outside Hyperbolic Pore
    rp = pore[3]
    Y = quad(f_cone,arcsinh(zmin/rp),arcsinh(zmax/rp),args=(block[1],block[2],block[3],zo/rp))
    return Y[0]/2/rp

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

###Functions for open segments
##Functions for interior segments named as Roout_j where j is the pore geometry type
def Roout_1(pore,zmin,zmax):  #Outside Cylindrical Pore
    rp = pore[2]
    Y = 1/pi*(arctan(zmax/rp)-arctan(zmin/rp))
    return Y/2/rp
def Roout_2(pore,zmin,zmax):  #Outside Conical Pore
    if zmin < 0:        #Bottom acces region contribution
        rp = pore[2]
    elif zmax > 0:      #Top access region contribution
        rp = pore[3]
    Y = 1/pi*(arctan(zmax/rp)-arctan(zmin/rp))
    return Y/2/rp
def Roout_3(pore,zmin,zmax):  #Outside Hyperbolic Pore
    rp = pore[3]
    Y = 1/pi*(arctan(zmax/rp)-arctan(zmin/rp))
    return Y/2/rp

##Functions for interior segments named as Roin_j where j is the pore geometry type
def Roin_1(pore,zmin,zmax):   #Inside Cylindrical Pore
    rp = pore[2]
    Y = 2/pi*(zmax/rp-zmin/rp)
    return Y/2/rp
def Roin_2(pore,zmin,zmax):   #Inside Conical Pore
    rmin = rp_con(pore,zmin)
    rmax = rp_con(pore,zmax)
    L = pore[1]
    r1 = pore[2]
    r2 = pore[3]
    return L/pi/(r2-r1)*(1/rmin-1/rmax)
def Roin_3(pore,zmin,zmax):   #Inside Hyperbolic Pore
    dL = pore[1]/pore[2]
    dr = pore[3]/pore[2]
    x1 = zmin/pore[2]
    x2 = zmax/pore[2]
    Y = 1/pi*dL/sqrt(dr**2-1)*(arctan(2*sqrt(dr**2-1)/dL*x2)-arctan(2*sqrt(dr**2-1)/dL*x1))
    return Y/2/pore[2]

########

###Defining Pore Characteristics
#[0, 0, rp] - 2D pore
#[1, Lp, rp] - Cylindrical Pore
#[2, Lp, r1, r2] - Conical Pore, r1 and r2 are bottom and top radii
#[3, Lp, rin, rout] - Hyperbolic Pore

###Defining Complex Molecules' subunit characteristics
#0 - Cylinder;          block = [0,lc,rc] 
#1 - Sphere;            block = [1,rs]
#2 - Ellipsoid;         block = [2,b,a]
#3 - Wedge;             block = [3,lw,r1,r2,phi]
#4 - Truncated Cone;    block = [4,lco,r1,r2]

#ToDo: Is block normalized?
def main(block,pore,resolution):
    #Molecule's sub-unit half-lengths and total length
    L_rad = [block[i][1] for i in range(len(block))]    
    L = 2*sum(L_rad)
    Lp = pore[1]

    ###Region-dependent Non-dimensionalization of blocks properties 

    ##Interior pore region normalization
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
        f_bot = pore[3]
    bnd_bot = [[block[i][j]/f_bot for j in range(len(block[i]))] for i in range(len(block))]
    for i in range(len(block)):
        bnd_bot[i][0] = block[i][0]
        if block[i][0] == 3:    #The angle of the wedged cylinder is normalized by 2pi instead
            bnd_bot[i][4] = block[i][4]/2/pi
            

    #Numerical values and initialization
    zz = linspace((-1.25*L)+(-2*Lp),(0.25*L)+(2*Lp),resolution,endpoint=True) #Array containing distances from pore denter to bottom of molecule
    Rbz = zeros(len(zz))    #Array will contain blocked resistance values for each zz normalized by open pore value

    #This loops through z and and through sub-units to determine which function to call 
    for i,z in enumerate(zz):
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
                Rb = Rb + globals()[func_name_out](pore,bnd_bot[j],zo+Lp/2,zmin+Lp/2,zmax+Lp/2)
            elif (zmin < -Lp/2) and (abs(zmax) < Lp/2): #Partially inside and under the pore
                Rb = Rb + globals()[func_name_in](pore,bnd_in[j],zo,-Lp/2,zmax)         #Interior contribution
                Rb = Rb + globals()[func_name_out](pore,bnd_bot[j],zo+Lp/2,zmin+Lp/2,0) #Bottom access region contribution
            elif (zmin < -Lp/2) and (zmax > Lp/2):      #Sub-unit longer than pore, spilling above and underneath pore 
                Rb = Rb + globals()[func_name_out](pore,bnd_top[j],zo-Lp/2,0,zmax-Lp/2) #Top access region contribution
                Rb = Rb + globals()[func_name_in](pore,bnd_in[j],zo,-Lp/2,Lp/2)         #Interior contribution
                Rb = Rb + globals()[func_name_out](pore,bnd_bot[j],zo+Lp/2,zmin+Lp/2,0) #Bottom access region contribution
            elif (zmin >= -Lp/2) and (zmax <= Lp/2):    #Sub-unit shorter than pore and completely inside the pore
                Rb = Rb + globals()[func_name_in](pore,bnd_in[j],zo,zmin,zmax)
            elif (abs(zmin) < Lp/2) and (zmax > Lp/2):  #Partially inside and above the pore
                Rb = Rb + globals()[func_name_in](pore,bnd_in[j],zo,zmin,Lp/2)          #Interior contribution
                Rb = Rb + globals()[func_name_out](pore,bnd_top[j],zo-Lp/2,0,zmax-Lp/2) #Top access region contribution
            if zmin >= Lp/2:                            #Completely above the pore
                Rb = Rb + globals()[func_name_out](pore,bnd_top[j],zo-Lp/2,zmin-Lp/2,zmax-Lp/2)

            if j != len(block):     #Centering zo around the next unit
                zo = zo + sum(L_rad[j:j+2])

        #Open Segment Contribution Calculations
        zmax = z + L
        ###Name of region-specific functions to be called 
        func_name_in = 'Roin_'+str(pore[0])
        func_name_out = 'Roout_'+str(pore[0])

        ##Testing whether molecule is inside or outside pore, and calling appropriate functions 
        if zmax <= -Lp/2:                           #Molecule completely under pore
            Rb = Rb + globals()[func_name_out](pore,0,inf)           #Empty Top Access Region
            Rb = Rb + globals()[func_name_in](pore,-Lp/2,Lp/2)       #Empty Pore
            Rb = Rb + globals()[func_name_out](pore,zmax+Lp/2,0)     #Bottom access region, above molecule
            Rb = Rb + globals()[func_name_out](pore,-inf,z+Lp/2)     #Bottom access region, under Molecule
        elif (z <= -Lp/2) and (abs(zmax) <= Lp/2):    #Moelcule partially inside and under the pore
            Rb = Rb + globals()[func_name_out](pore,0,inf)           #Empty top access region
            Rb = Rb + globals()[func_name_in](pore,zmax,Lp/2)        #Inside Pore, above molecule
            Rb = Rb + globals()[func_name_out](pore,-inf,z+Lp/2)     #Bottom access region, under Molecule
        elif (z >= -Lp/2) and (zmax <= Lp/2):         #Molecule shorter and completely inside the pore
            Rb = Rb + globals()[func_name_out](pore,0,inf)           #Empty top access region
            Rb = Rb + globals()[func_name_in](pore,zmax,Lp/2)        #Inside Pore, above molecule
            Rb = Rb + globals()[func_name_in](pore,-Lp/2,z)          #Inside Pore, under molecule
            Rb = Rb + globals()[func_name_out](pore,-inf,-0)         #Empty bottom access region
        elif (z <= -Lp/2) and (zmax >= Lp/2):         #Molecule longer than pore, spilling above and underneath pore 
            Rb = Rb + globals()[func_name_out](pore,zmax-Lp/2,inf)   #Above Molecule
            Rb = Rb + globals()[func_name_out](pore,-inf,z+Lp/2)     #Under Molecule
        elif (abs(z) <= Lp/2) and (zmax >= Lp/2):     #Molecule partially inside and above the pore
            Rb = Rb + globals()[func_name_out](pore,zmax-Lp/2,inf)   #Top access region, above Molecule
            Rb = Rb + globals()[func_name_in](pore,-Lp/2,z)          #Inside Pore, under molecule
            Rb = Rb + globals()[func_name_out](pore,-inf,-0)         #Empty bottom access region 
        if z >= Lp/2:                                #Molecule completely above pore
            Rb = Rb + globals()[func_name_out](pore,zmax-Lp/2,inf)   #Top access region, Above Molecule
            Rb = Rb + globals()[func_name_out](pore,0,z-Lp/2)        #Top access region, Under Molecule
            Rb = Rb + globals()[func_name_in](pore,-Lp/2,Lp/2)       #Empty Pore
            Rb = Rb + globals()[func_name_out](pore,-inf,-0)         #Empty bottom access region

        ##Updating resistance before loop end
        Rbz[i] = Rb
        i = i+1

    #Normalizing by open pore resistance
    Racc = globals()['Roout_'+str(pore[0])](pore,0,inf) + globals()['Roout_'+str(pore[0])](pore,-inf,-0)
    Rpore = globals()['Roin_'+str(pore[0])](pore,-Lp/2,Lp/2)
    Ropen = Racc+Rpore
    GbGo = (Rbz/Ropen)**-1
    X = zz-mean(zz)
    return X,GbGo


if __name__ == "__main__":
    #User-Defined Pore
    # pore = [1,20,4.45]
    # pore = [0,0,4.45]
    pore = [2, 50, 1,5]
    #pore = [1, 10, 1]
    
    #User-Defined Complex Structure
    #block = [[0,100,0.99]]
    #block = [[0,10,0.25],[1,0.5],[0,10,0.25],[1,0.5],[0,10,0.25]]
    #block = [[1,0.5]]
    ##SpeedBump
    #block = [[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1],[0,93,sqrt(3)*1.1],[0,274.5,1.1]]
    #ShootingStar
    #block = [[0,16,sqrt(6)*1.1],[0,300,1.1]]
    #block = [[0,16,sqrt(6)*1.1],[0,1033,1.1]]
    #Tests
    #block = [[0, 100, 0.75]]
    #block = [[1, 0.9]]
    #block = [[2,5,0.9]]
    #block = [[3,10,0.2,0.8,pi/3]]
    block = [[4,12,0.2,0.9]]
    X,GbGo = main(block,pore,20000)
    plt.plot(X,GbGo)
    plt.show()
