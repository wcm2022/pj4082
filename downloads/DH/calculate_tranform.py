def Tdh(alpha, a, d, q):
    DHtransform = Matrix([
        [            cos(q),           -sin(q),           0,             a],
        [ sin(q)*cos(alpha), cos(q)*cos(alpha), -sin(alpha), -sin(alpha)*d],
        [ sin(q)*sin(alpha), cos(q)*sin(alpha),  cos(alpha),  cos(alpha)*d],
        [                 0,                 0,           0,             1]])
    return DHtransform
    
def transformbuild(DHparam):
    totaltransform = eye(4)

    print("Building transforms from given DH parameter table")

    for x in range(0,DHparam.rows):
        transform = Tdh(DHparam[x,0], DHparam[x,1], DHparam[x,2], DHparam[x,3])
        totaltransform = totaltransform*transform
        print("Transform matrix from frame %s to %s complete" %(x,x+1))
    
    print("Total DH tranform complete. Simplifying")
    totaltransform = simplify(totaltransform)
    print("Simplify and build complete.")
    
    return totaltransform