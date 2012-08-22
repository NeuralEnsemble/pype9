"""

  This package contains code to visualise the data

  
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2011 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

import math
import numpy.random
from numpy.linalg import norm
from mpl_toolkits.mplot3d import Axes3D
from itertools import product, combinations

def tube_mesh(track, radius, num_edges=80):
    """
    Will generate a mesh for a tube around the given track of points, with the given radius.
    
    @param track: The track of points the tube will be created around
    @param raius: The radius of the tube to create
    @param num_edges: The number of edges to place around the diameter of the tube (the higher the number, the higher the quality, yet slower to render)
    """
    if numpy.isnan(track).any():
        raise Exception("Track has NaN values")
    num_control_points = len(track)
    segs = track[1:num_control_points, :] - track[0:num_control_points - 1, :]

    norm_segs = numpy.zeros(segs.shape)
    length_segs = numpy.sqrt(numpy.sum(segs * segs, axis=1))
    zero_mask = length_segs == 0.0
    length_segs[zero_mask] = 0.0001
    segs[zero_mask] = 0.0001
    track[zero_mask] = track[zero_mask] + 0.0001
    norm_segs[:, 0] = segs[:, 0] / length_segs
    norm_segs[:, 1] = segs[:, 1] / length_segs
    norm_segs[:, 2] = segs[:, 2] / length_segs

#        consec_segs_align = norm_segs[1:num_control_points - 2, :].dot(norm_segs[2:num_control_points - 1, :], axis=1)

    found_suitable = None
    for i in xrange(100): #@UnusedVariable

        ref_vector = numpy.random.normal(size=3)

        (t, n, b) = frenet_frame(track[:, 0], track[:, 1], track[:, 2], ref_vector)

        if not numpy.isnan(n).any():
            found_suitable = True
            break

    if not found_suitable:
        raise Exception("Could not find suitable reference vector for track")

    X = numpy.zeros((num_control_points, num_edges))
    Y = numpy.zeros((num_control_points, num_edges))
    Z = numpy.zeros((num_control_points, num_edges))
    edge_incr = 2 * math.pi / (num_edges - 1)
    theta = numpy.arange(0, 2 * math.pi + edge_incr / 2.0, edge_incr)

    w = numpy.zeros((1, 3))

    for point_i in xrange(num_control_points):

        if point_i == 0:
            w = track[0, :] + n[0, :]
            n_prime = n[0, :]
            b_prime = b[0, :]

        else:
            mu = numpy.sum(t[point_i, :] * (track[point_i, :] - w)) / numpy.sum(t[point_i, :] * segs[point_i - 1, :])
            w_proj = w + mu * segs[point_i - 1, :]
            n_prime = w_proj - track[point_i, :]
            n_prime = n_prime / norm(n_prime)
            b_prime = numpy.cross(t[point_i, :], n_prime)
            b_prime = b_prime / norm(b_prime)
            w = track[point_i, :] + n_prime

        X[point_i, :] = track[point_i, 0] + radius * (n_prime[0] * numpy.cos(theta) + b_prime[0] * numpy.sin(theta))
        Y[point_i, :] = track[point_i, 1] + radius * (n_prime[1] * numpy.cos(theta) + b_prime[1] * numpy.sin(theta))
        Z[point_i, :] = track[point_i, 2] + radius * (n_prime[2] * numpy.cos(theta) + b_prime[2] * numpy.sin(theta))

    return (X, Y, Z)



def ellipse_tube_mesh(track, x_scale, y_scale, num_edges=80):
    """
    Will generate a mesh for a tube around the given track of points, with the given radius.
    
    @param track: The track of points the tube will be created around
    @param raius: The radius of the tube to create
    @param num_edges: The number of edges to place around the diameter of the tube (the higher the number, the higher the quality, yet slower to render)
    """
    if numpy.isnan(track).any():
        raise Exception("Track has NaN values")
    num_control_points = len(track)
    segs = track[1:num_control_points, :] - track[0:num_control_points - 1, :]

    norm_segs = numpy.zeros(segs.shape)
    length_segs = numpy.sqrt(numpy.sum(segs * segs, axis=1))
    zero_mask = length_segs == 0.0
    length_segs[zero_mask] = 0.0001
    segs[zero_mask] = 0.0001
    track[zero_mask] = track[zero_mask] + 0.0001
    norm_segs[:, 0] = segs[:, 0] / length_segs
    norm_segs[:, 1] = segs[:, 1] / length_segs
    norm_segs[:, 2] = segs[:, 2] / length_segs

#        consec_segs_align = norm_segs[1:num_control_points - 2, :].dot(norm_segs[2:num_control_points - 1, :], axis=1)

    (t, n, b) = frenet_frame(track[:, 0], track[:, 1], track[:, 2], numpy.array((0.0, 1.0, 0.0)))

    X = numpy.zeros((num_control_points, num_edges))
    Y = numpy.zeros((num_control_points, num_edges))
    Z = numpy.zeros((num_control_points, num_edges))
    edge_incr = 2 * math.pi / (num_edges - 1)
    theta = numpy.arange(0, 2 * math.pi + edge_incr / 2.0, edge_incr)

    w = numpy.zeros((1, 3))

    for point_i in xrange(num_control_points):

        if point_i == 0:
            w = track[0, :] + n[0, :]
            n_prime = n[0, :]
            b_prime = b[0, :]

        else:
            mu = numpy.sum(t[point_i, :] * (track[point_i, :] - w)) / numpy.sum(t[point_i, :] * segs[point_i - 1, :])
            w_proj = w + mu * segs[point_i - 1, :]
            n_prime = w_proj - track[point_i, :]
            n_prime = n_prime / norm(n_prime)
            b_prime = numpy.cross(t[point_i, :], n_prime)
            b_prime = b_prime / norm(b_prime)
            w = track[point_i, :] + n_prime

        X[point_i, :] = track[point_i, 0] + x_scale * n_prime[0] * numpy.cos(theta) + y_scale * b_prime[0] * numpy.sin(theta)
        Y[point_i, :] = track[point_i, 1] + x_scale * n_prime[1] * numpy.cos(theta) + y_scale * b_prime[1] * numpy.sin(theta)
        Z[point_i, :] = track[point_i, 2] + x_scale * n_prime[2] * numpy.cos(theta) + y_scale * b_prime[2] * numpy.sin(theta)

    return (X, Y, Z)

def frenet_frame(x, y, z, vec):
    """
    FRAME Calculate a Frenet-like frame for a polygonal space curve
    (t,n,b)=frame(x,y,z,v) returns the tangent unit vector, a normal
    and a binormal of the space curve x,y,z. The curve may be a row or
    column vector, the frame vectors are each row vectors. 
    
    This function calculates the normal by taking the cross product
    of the tangent with the vector v if v is chosen so that it is
    always far from t the frame will not twist unduly.
    
    If two points coincide, the previous tangent and normal will be used.
    
    Written for MATLAB by Anders Sandberg, asa@nada.kth.se, 2005, 
    converted to python by Thomas G Close, tclose@oist.jp
    """
    N = len(x)
    if len(y) != N or len(z) != N:
        raise Exception("Length of x (%d), y (%d) an z (%d) arguments do not match"
                                                                        % (len(x), len(y), len(z)))
    t = numpy.zeros((N, 3))
    b = numpy.zeros((N, 3))
    n = numpy.zeros((N, 3))
    p = numpy.zeros((N, 3))
    p[:, 0] = x
    p[:, 1] = y
    p[:, 2] = z

    for i in range(1, N - 1):
        t[i, :] = p[i + 1, :] - p[i - 1, :]
        tl = norm(t[i, :])
        if tl > 0:
            t[i, :] = t[i, :] / tl
        else:
            t[i, :] = t[i - 1, :]

    t[0, :] = p[1, :] - p[0, :]
    t[0, :] = t[0, :] / norm(t[0, :])
    t[N - 1, :] = p[N - 1, :] - p[N - 2, :]
    t[N - 1, :] = t[N - 1, :] / norm(t[N - 1, :])

    for i in range(1, N - 1):
        n[i, :] = numpy.cross(t[i, :], vec)
        nl = norm(n[i, :])
        if nl > 0:
            n[i, :] = n[i, :] / nl
        else:
            n[i, :] = n[i - 1, :]

    n[0, :] = numpy.cross(t[0, :], vec)
    n[0, :] = n[0, :] / norm(n[0, :])
    n[N - 1, :] = numpy.cross(t[N - 1, :], vec)
    n[N - 1, :] = n[N - 1, :] / norm(n[N - 1, :])

    for i in range(N):
        b[i, :] = numpy.cross(t[i, :], n[i, :])
        b[i, :] = b[i, :] / norm(b[i, :])

    return (t, n, b)

def draw_bounding_box(ax, min_bounds, max_bounds):
    #draw cube
    rx = min_bounds[0], max_bounds[0]
    ry = min_bounds[1], max_bounds[1]
    rz = min_bounds[2], max_bounds[2]
    min_bounds = numpy.array(min_bounds)
    max_bounds = numpy.array(max_bounds)
    for s, e in combinations(numpy.array(list(product(rx, ry, rz))), 2):
        if numpy.count_nonzero(numpy.abs(s - e) == max_bounds - min_bounds) == 1:
            ax.plot3D(*zip(s, e), color="b")

def draw_sphere(ax):
    #draw sphere
    u, v = numpy.mgrid[0:2 * numpy.pi:20j, 0:numpy.pi:10j]
    x = numpy.cos(u) * numpy.sin(v)
    y = numpy.sin(u) * numpy.sin(v)
    z = numpy.cos(v)
    ax.plot_wireframe(x, y, z, color="r")

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.set_aspect("equal")
    draw_bounding_box(ax, [0, 0, 0], [1, 2, 3])
    plt.show()
