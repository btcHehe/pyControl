import numpy as np
import matplotlib.pyplot as plt
import time_response as Tresp
from math import log

# denumerator and numerator coefficients must be given in a specific order:
#   numerator: a1*s^n + a2*s^(n-1) + a3*s^(n-2) + a4*s^(n-3) + ... + an =>  [a1, a2, a3, a4, ..., an]
#   denumerator: s^n + b1*s^(n-1) + b2*s^(n-2) + b3*s^(n-3) + ... + bn => [b1, b2, b3, ..., bn]

class sys:
    def __init__(self):
        self.A = np.array([])
        self.B = np.array([])
        self.C = np.array([])
        self.D = np.array([])
        self.TFnumerator = np.array([])
        self.TFdenumerator = np.array([])
        self.startCond = np.array([])

    # diagonal form
    def diag(self):  # TODO fix this
        eigVals, eigVecs = np.linalg.eig(self.A)
        P = np.empty((np.size(eigVals), 0))  # transformation matrix
        for eigenVector in eigVecs:
            P = np.column_stack((P, eigenVector))
        invP = np.linalg.inv(P)
        A = np.matmul(invP, np.matmul(self.A, P))
        B = np.matmul(invP, self.B)
        C = np.matmul(self.C, P)
        return A, B, C

    # observable canonical form of SISO system
    # highest power of the s in denumerator must be bigger than highest power in the numerator
    # highest power of s in denumerator must have coefficient equal 1
    def obsv(self):
        if(self.TFdenumerator[0][0] == 1):
            self.TFdenumerator = self.TFdenumerator[0][1:]
        numCols = np.size(self.TFnumerator)
        denCols = np.size(self.TFdenumerator) 
        if denCols > numCols:  # making numerator and denumerator equal length filling with 0
            tempArr = np.zeros(denCols)
            tempArr[denCols - numCols:] = self.TFnumerator
            self.TFnumerator = tempArr
        elif denCols < numCols:
            raise Exception('denumerator must be higher order than numerator')
        obsvA = np.array([-1 * self.TFdenumerator]).transpose() # column of minus denumerator values
        subMat = np.identity(denCols - 1)  # identity matrix
        subMat = np.vstack((subMat, np.zeros(denCols - 1)))  # row of 0 added to identity matrix
        obsvA = np.append(obsvA, subMat, axis=1)
        obsvB = self.TFnumerator[..., None]  # column of numerator values
        obsvC = np.array([1])
        obsvC = np.append(obsvC, np.zeros(denCols - 1), axis=0)  # row of 0
        return obsvA, obsvB, obsvC

    # controllable canonical form of SISO system
    # highest power of the s in denumerator must be bigger than highest power in the numerator
    # highest power of s in denumerator must have coefficient equal 1
    def contr(self):
        numCols = np.size(self.TFnumerator)
        denCols = np.size(self.TFdenumerator)
        if denCols > numCols:  # making numerator and denumerator equal length filling with 0
            tempArr = np.zeros(denCols)
            tempArr[denCols - numCols:] = self.TFnumerator
            self.TFnumerator = tempArr
        elif denCols < numCols:
            raise Exception('denumerator must be higher order than numerator')
        contA = np.zeros(denCols - 1)[..., None]  # column of 0
        subMat = np.identity(denCols - 1)  # identity matrix
        contA = np.append(contA, subMat, axis=1)
        contA = np.append(contA, -1 * self.TFdenumerator, axis=0)  # row of minus denumerator values
        contB = np.zeros(denCols - 1)[..., None]  # column of 0
        contB = np.vstack((contB, np.array([1])))
        contC = np.array(self.TFnumerator)  # row of numerator values
        return contA, contB, contC


class ss(sys):
    def __init__(self, A, B, C, D, stCond=None):
        super().__init__()
        if stCond is None:
            stCond = []
        self.A = np.array(A)
        tempB = np.array(B)
        self.B = np.reshape(tempB, (np.shape(tempB)[0],1))
        self.C = np.array(C)
        self.D = np.array(D)
        if np.size(np.array(stCond)) < np.size(A, axis=0):  # if starting conditions vector is too short
            self.startCond = np.array(stCond)
            for i in range(np.size(A, axis=0) - np.size(self.startCond)):
                np.append(self.startCond, np.array([0]))
        else:
            raise Exception('number of starting conditions must be equal to the order of the system')


class tf(sys):
    def __init__(self, num, denum):
        super().__init__()
        self.TFnumerator = np.array(num)
        self.TFdenumerator = np.array(denum)


#returns ss system in a observable canonical form based on given tf
def tf2ss(system):
    if isinstance(system, tf):
        if(system.TFdenumerator[0][0] != 1):
            system.TFnumerator = system.TFnumerator / system.TFdenumerator[0][0]   #keeping the coefficient of the highest s (s^n) equal to 1
            system.TFdenumerator = system.TFdenumerator / system.TFnumerator[0][0]
        A, B, C = system.obsv()
        D = np.array([0])
        systemSS = ss(A, B, C, D)
        return systemSS
    else:
        raise Exception('you need to pass tf system as the argument')

def ss2tf(system):
    if isinstance(system, ss):
        pass
    else:
        raise Exception('you need to pass ss system as the argument')


#returns array of poles of system
def poles(system):
    roots = np.array([])
    if isinstance(system, tf):
        roots = np.roots(system.TFdenumerator)
    elif isinstance(system, ss):
        roots, eigvecs = np.linalg.eig(system.A)
    else:
        raise Exception('argument must be tf or ss system')
    return roots

#returns array of zeros of system
def zeros(system):
    if isinstance(system, tf):
        roots = np.roots(system.TFnumerator)
    elif isinstance(system, ss):
        roots, eigvecs = np.linalg.eig(system.A)
    else:
        raise Exception('argument must be tf or ss system')
    return roots



#returns stateTrajectory matrix for system
def stateTrajectory(system):
    Y = T = X = np.array([])
    if isinstance(system, tf):
        systemSS = tf2ss(system)
        stateTrajectory(systemSS)
    elif isinstance(system, ss):
        Y,T,X = Tresp.solveTrap(system, 1)
        return X
    else:
        raise Exception('argument must be a tf or ss system')


#takes system and returns tuple of vectors (Y,T,X) - response and time vectors and state trajectory matrix
def step(system, plot = False, solver = 'trap'):
    Y = T = X = np.array([])
    if isinstance(system, tf):
        systemSS = tf2ss(system)
        step(systemSS)
    elif isinstance(system, ss):
        if solver == 'ee':             #explicit (forward) Euler
            Y,T,X = Tresp.solveEE(system, 1)
        elif solver == 'ie':           #implicit (backward) Euler
            Y,T,X = Tresp.solveIE(system, 1)
        elif solver == 'trap':         #trapezoidal
            Y,T,X = Tresp.solveTrap(system, 1)
        elif solver == 'rk4':
            Y,T,X = Tresp.solveRK4(system, 1)
        else:
            raise Exception('wrong solver chosen, choose: ee, ie, trap or rk4')
        if plot:
            fig = plt.figure()
            ax = fig.add_subplot()
            ax.plot(T,Y)
            ax.set_title('Step response')
            ax.set_ylabel('y(t)')
            ax.set_xlabel('t [s]')
            plt.show()
        else:
            return (Y,T,X)
    else:
        raise Exception('argument must be a tf or ss system')


#draws phase plot on phase plane of min 2nd order system, var1 and var2 describes which state variables need to be plot:
# 0 - x1
# 1 - x2 etc.
def phasePlot(system, var1=0, var2=1):
    if isinstance(system, tf):
        systemSS = tf2ss(system)
        phasePlot(systemSS, var1, var2)
    elif isinstance(system, ss):
        if np.shape(system.A)[0] >= 2:
            Y = T = X = np.array([])
            Y,T,X = Tresp.solveTrap(system, 1)
            fig = plt.figure()
            ax = fig.add_subplot()
            ax.plot(X[var1], X[var2])
            ax.set_title('Phase plot')
            ax.set_ylabel(f'x{var1+1}(t)')
            ax.set_xlabel(f'x{var2+1}(t)')
            plt.show()
        else:
            raise Exception('system needs to be at least 2nd order')


#TODO:
#python's pow() function couldn't handle complex numbers and was trying to cast it into something else
def __imagPow(base, power):
    res = 1
    for i in range(power-1):
        res *= base
    return res

#creates sinusodial transfer function G(jw)
def __sinTF(system):
    num = []
    den = []
    if isinstance(system, tf):
        for i in range(len(system.TFnumerator)):
            num.append(complex(system.TFnumerator[i], 0))
        for i in range(len(system.TFdenumerator)):
            den.append(complex(system.TFdenumerator[i], 0))
        for i in range(len(num)):
            num[i] = num[i]*__imagPow(1j, len(num)-i)
        for k in range(len(den)):
            den[k] = den[k]*__imagPow(1j, len(den)-k)
        return (num, den)
    elif isinstance(system, ss):
        systemTF = ss2tf(system)
        __sinTF(systemTF)



#draws nyquist plot of system
def nyquist(system):
    pass

#draws bode diagrams for system
def bode(system):
    n,d = __sinTF(system)
    num = den = 0
    Gvec = np.array([])
    Phvec = np.array([])
    Wvec = np.array([])
    #calculating the amplitude and phase characteristics
    for w in np.linspace(0.1,1000,20000):
        for i in range(len(n)):
           num += n[i]*pow(w,len(n)-i) 
        for k in range(len(d)):
           den += d[k]*pow(w,len(d)-k)
        G = 20*log(abs(num/den))
        Ph = np.angle((num/den), deg=True)
        Wvec = np.append(Wvec, w)
        Gvec = np.append(Gvec, G)
        Phvec = np.append(Phvec, Ph)
    fig,ax = plt.subplots(2)
    ax[0].set_title('Bode diagrams')
    ax[0].set_ylabel('Magnitude [dB]')
    ax[0].set_xlabel('ω [rad/s]')
    ax[0].set_xscale('log')
    ax[1].set_ylabel('Phase shift [°]')
    ax[1].set_xlabel('ω [rad/s]')
    ax[1].set_xscale('log')
    ax[0].plot(Wvec, Gvec)
    ax[1].plot(Wvec, Phvec)
    plt.show()


