import time
start = time.time()
from numpy import sign, sqrt, tanh, sinh, cosh, pi, linspace, zeros, arctan, arcsinh
import numba
from scipy.integrate import quad
from scipy.special import ellipkinc
from misc import BlockNormalizer

start = time.time()
ipi = 1/pi

numbaParams = {
    "fastmath": False,
    "cache": True,
}

@numba.njit("f8(f8,f8,f8)",**numbaParams)
def i_sphere(mu,ds,x):
    sechmu2 = 1/(cosh(mu)**2)
    denominator = sqrt(1 - ((ds**2 + x**2)*sechmu2) + (2*x**2) - (2*x*tanh(mu)*sqrt(1+x**2-ds**2*sechmu2)))
    if denominator == 0:
        return 0
    return sechmu2/denominator

@numba.njit("f8(f8,f8,f8,f8,f8)",**numbaParams)
def i_cone(mu,d1,d2,dl,x):
    sechmu2 = 1/cosh(mu)
    D = sqrt(1 - ( ( 2*dl/(d2-d1) ) * ( (dl*(d2+d1)/(d2-d1)) - x )  +  sign(mu*(d2-d1)) * sqrt(( tanh(mu)**2 + (4*dl**2)/(d2-d1)**2 )*sinh(mu)**2 - ( tanh(mu)**2 * (x-dl*(d2+d1)/(d2-d1))**2 ) ) )**2 / (cosh(mu)**2 * (tanh(mu)**2 + (4*dl**2)/(d2-d1)**2)**2))
    if D == 0:
        return 0
    return sechmu2/D

@numba.njit("f8(f8,f8,f8,f8)",**numbaParams)
def i_wedge(mu,d1,d2,dphi):
    sechmu2 = 1/cosh(mu)
    denominator = (1-dphi)*sqrt(1-sechmu2**2*d1**2) + dphi*sqrt(1-sechmu2**2*d2**2)
    if denominator == 0:
        return 0
    return sechmu2/denominator

@numba.njit("f8(f8,f8,f8,f8)",**numbaParams)
def i_ellipsoid(mu,da,db,x):
    sechmu = 1/cosh(mu)
    i_S = (tanh(mu)**2 - (db/da)**2)*(db**2 + x**2 - sinh(mu)**2) +   (db*x/da)**2 + da**2*(tanh(mu)**2 - (db/da)**2)**2
    if i_S < 0:
        i_S = 0
    i_N = (tanh(mu)**2 - (db/da)**2)*(db**2 + x**2 - sinh(mu)**2) + 2*(db*x/da)**2 - sign(mu)*2*(db/da)*x*sqrt(i_S)
    i_D = (tanh(mu)**2 - (db/da)**2)**2 * cosh(mu)**2
    if i_D == 0:
        return 0
    D = sqrt(1 + i_N/i_D)
    if D == 0:
        return 0
    return sechmu/D

# Ellipsoid backup
@numba.njit("f8(f8,f8,f8,f8,f8)", fastmath=True)
def unnormalized_ellipsoid(mu,b,a,rp,zo):
    den = 1+(((tanh(mu))**2-b**2/a**2)*((b**2+zo**2)/rp**2-(sinh(mu))**2)+2*(zo*b/rp/a)**2-sign(mu)*2*zo*b/rp/a*sqrt(((tanh(mu))**2-b**2/a**2)*((b**2+zo**2)/rp**2-(sinh(mu))**2)+(zo*b/rp/a)**2+a**2/rp**2*((tanh(mu))**2-b**2/a**2)**2))/((tanh(mu))**2-b**2/a**2)**2/(cosh(mu))**2
    res = 1/sqrt(den)/cosh(mu)
    return res

print(f"Load Time: {time.time()-start}")
start = time.time()

def main(block, rp, resolution):
    global store
    """
    All length/2 calculations are pre-handled by blockmaker
    The block is a list of lists, each list containing the shape and the dimensions of Complex Molecules
    
    ##Complex Molecules - Test Code Including every type of building block 
    0 - Cylinder;          block = [0,lc,rc] Fix Length stuff  (lc = half length of cylender)
    1 - Sphere;            block = [1,rs] 
    2 - Ellipsoid;         block = [2,b,a]
    3 - Wedge;             block = [3,lw,r1,r2,phi] (lw = half length of cylender) (phi = radians)
    4 - Truncated Cone;    block = [4,lco,r1,r2] (loc = half length of cylender)
    """
    L_rad = [block[i][1] for i in range(len(block))]
    L = 2*sum(L_rad)
    zz = linspace((-1.25*L)+(-3*rp),(0.25*L)+(3*rp),resolution,endpoint=True)
    RbRo = zeros(len(zz))
    threshold = 5000*rp
    # Normalize the blocks
    block = BlockNormalizer(block, rp)
    #Let z be the distance from the obstruction minimum to the pore
    for i,z in enumerate(zz):
        Rb = 0
        # Center of shape
        z0 = z+L_rad[0]
        for j in range(len(block)):
            x = z0/rp
            if z0+L_rad[j]<-threshold or z0-L_rad[j]>threshold:
                ...
            else:
                if block[j][0] == 1:    #Sphere
                    ds = block[j][1]
                    integral = quad(i_sphere,arcsinh(x-ds),arcsinh(x+ds),args=(ds,x))[0]
                elif block[j][0] == 2:  #Ellipsoid
                    db = block[j][1]
                    da = block[j][2]
                    integral = quad(i_ellipsoid,arcsinh(x-db),arcsinh(x+db),args=(da,db,x))[0]
                    # integral = quad(f_ellipsoid,arcsinh(x-db),arcsinh(x+db),args=(db*rp,da*rp,rp,x*rp))[0] # Works
                elif block[j][0] == 3:  #Wedge
                    dl = block[j][1]
                    d1 = block[j][2]
                    d2 = block[j][3]
                    dphi = block[j][4]
                    integral = quad(i_wedge,arcsinh(x-dl),arcsinh(x+dl),args=(d1,d2,dphi))[0]
                elif block[j][0] == 4:  #Truncated Cone 
                    dl = block[j][1]
                    d1 = block[j][2]
                    d2 = block[j][3]
                    integral = quad(i_cone,arcsinh(x-dl),arcsinh(x+dl),args=(d1,d2,dl,x))[0]
                else:
                    integral = 0
                Rb = Rb + integral
            z0 = z0 + sum(L_rad[j:j+2]) #Centering z0 around the next unit
        RbRo[i] = Rb
        
    #Analytical Cylindrical Part
    z0 = zz + L_rad[0]
    for j in range(len(block)):
        if block[j][0] == 0:
            x = z0/rp
            dl = block[j][1]
            dr = block[j][2]
            RbRo += ellipkinc(pi/2-arctan(x-dl),dr**2) - ellipkinc(pi/2-arctan(x+dl),(dr)**2)
        z0 = z0 + sum(L_rad[j:j+2])
            
    #Unobstrocted Segments Contribution
    GbGo = (1+ipi*arctan(zz/rp)-ipi*arctan((zz+L)/rp)+ipi*RbRo)**-1
    return (zz+L/2), GbGo

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import winsound
    import numpy as np
    import sys, os
    np.seterr(all='raise')
    store = []
    # block = [[4,5,0,0.35],[0,5,0.6],[1,0.7],[0,2,0.23],[3,4,0.23,0.9,pi/10],[0,2.5,0.23],[3,4,0.23,0.9,pi/10],[0,7,0.23]]*100
    # block = [[4, 0.5, 2.0, 1.0]] # breaking wrong length
    # block = [[0, 1.0, 1.0], [1, 2.0], [0, 1.0, 2.0]] # working
    block = [[0, 100_000_0, 0.1],[1,1.0]] # breaking sphere
    resolution = 100_000_000
    # block = [[0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0], [0, 0.5, 1.0], [1, 1.0], [3, 1.5, 1.0, 1.0, 2.0]]
    block = [[0, 0.5, 2.99], [0, 0.5, 1.0], [2, 4.0, 2.0], [2, 4.0, 2.9]] # Debug Ellipsoid
    resolution = 1000
    rp = 3
    try:
        x, y = main(block, rp, resolution)
    except Exception as e:
        raise
    finally:
        # winsound.Beep(500, 1000)
        sys.stdout = sys.__stdout__
        # plt.scatter(range(len(GLOBAL["mu"])), GLOBAL["mu"], label="mu",s=0.1)
        # plt.scatter(range(len(GLOBAL["temp_A"])), GLOBAL["temp_A"], label="temp_A",s=0.1)
        # plt.scatter(range(len(GLOBAL["temp_B"])), GLOBAL["temp_B"], label="temp_B",s=0.1)
        # plt.legend()
        # plt.show()
        print(f"Execution Time: {time.time()-start}")
    print("Any values greater than 1: ", np.any(y>1))
    print(np.max(y))
    plt.plot(x, y)
    plt.show()
    # save store in a csv
    import pandas as pd
    df = pd.DataFrame(store)
    idx = "new"
    df.columns = [f"{idx}_{col}" for col in df.columns]
    try:
        old = pd.read_csv("store.csv")
    except:
        old = pd.DataFrame()
    for col in df.columns:
        if col in old.columns:
            del old[col]
    df = pd.concat([old, df], axis=1)
    df.to_csv("store.csv", index=False)
