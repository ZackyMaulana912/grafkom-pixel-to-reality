"""Quaternions and Euler angles, from scratch (standard library only).

Conventions (the 3D half of the ones fixed in fk.py):
- A quaternion is a tuple (w, x, y, z); a rotation quaternion has norm 1.
- Angles are degrees in the public API.
- Matrices act on column vectors. An Euler order is written as the matrix product
  from left to right: order "ZYX" means M = Rz(roll) @ Ry(yaw) @ Rx(pitch).
  Pitch is about x, yaw about y, roll about z.
- Reading M = Rz Ry Rx on a vector: Rx acts first, then Ry, then Rz, each about the
  FIXED world axis (extrinsic X, Y, Z). The same matrix is the intrinsic sequence
  Z, then Y', then X'' about the body's own axes. Either way the MIDDLE factor (yaw
  here) is the one that locks at +-90 deg.
- Godot's Node3D default is intrinsic YXZ = Ry @ Rx @ Rz, order "YXZ" here, whose
  middle axis is x (pitch). Always say which order when comparing with Godot.
"""
from __future__ import annotations

import math

IDENTITY = (1.0, 0.0, 0.0, 0.0)
AXES = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}
ANGLE_NAME = {"X": "pitch", "Y": "yaw", "Z": "roll"}


# --- quaternion algebra -----------------------------------------------------

def quat_mul(a, b):
    """Hamilton product a * b (apply b first, then a, when rotating vectors)."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def quat_conj(q):
    w, x, y, z = q
    return (w, -x, -y, -z)


def quat_dot(a, b):
    return sum(p * q for p, q in zip(a, b))


def quat_norm(q):
    return math.sqrt(quat_dot(q, q))


def quat_normalize(q):
    n = quat_norm(q)
    return tuple(c / n for c in q)


def quat_from_axis_angle(axis, angle_deg):
    """Unit quaternion turning angle_deg about axis (the axis need not be unit length)."""
    ax, ay, az = axis
    n = math.sqrt(ax * ax + ay * ay + az * az)
    half = math.radians(angle_deg) / 2.0
    s = math.sin(half) / n
    return (math.cos(half), ax * s, ay * s, az * s)


def quat_to_axis_angle(q):
    """(unit axis, angle_deg in [0, 360)) of a unit quaternion."""
    w, x, y, z = q
    angle = 2.0 * math.degrees(math.acos(max(-1.0, min(1.0, w))))
    s = math.sqrt(max(0.0, 1.0 - w * w))
    if s < 1e-12:
        return (0.0, 0.0, 1.0), angle  # no rotation: any axis will do
    return (x / s, y / s, z / s), angle


def quat_rotate(q, v):
    """Rotate vector v by q as q v q*. If |q| = s the result is also scaled by s^2."""
    w, x, y, z = quat_mul(quat_mul(q, (0.0, *v)), quat_conj(q))
    return (x, y, z)


def quat_to_matrix(q):
    """3 x 3 rotation matrix of a unit quaternion (columns = images of the x, y, z axes)."""
    cols = [quat_rotate(q, AXES[k]) for k in "XYZ"]
    return [[cols[j][i] for j in range(3)] for i in range(3)]


def slerp(q0, q1, t):
    """Spherical linear interpolation between unit quaternions, along the shorter arc.

    Walks the great circle at constant speed, so the rotation angle grows linearly in t.
    Very close inputs fall back to a normalised linear blend, where the arc and the
    chord are the same to rounding and sin(theta) would be close to 0.
    """
    cos_theta = quat_dot(q0, q1)
    if cos_theta < 0.0:  # q and -q are the same rotation; take the short way
        q1, cos_theta = tuple(-c for c in q1), -cos_theta
    if cos_theta > 0.9995:
        return quat_normalize(tuple(a + t * (b - a) for a, b in zip(q0, q1)))
    theta = math.acos(cos_theta)
    k0 = math.sin((1.0 - t) * theta) / math.sin(theta)
    k1 = math.sin(t * theta) / math.sin(theta)
    return tuple(k0 * a + k1 * b for a, b in zip(q0, q1))


# --- Euler angles -----------------------------------------------------------

def axis_matrix(axis, angle_deg):
    """Rx, Ry or Rz for axis in "XYZ"."""
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    if axis == "X":
        return [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]
    if axis == "Y":
        return [[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]]
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mat_vec(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def mat_max_diff(a, b):
    return max(abs(a[i][j] - b[i][j]) for i in range(3) for j in range(3))


def euler_to_matrix(pitch_deg, yaw_deg, roll_deg, order="ZYX"):
    """M = product of the three axis matrices in `order`, left to right (see module docstring)."""
    angle = {"X": pitch_deg, "Y": yaw_deg, "Z": roll_deg}
    m = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    for axis in order:
        m = mat_mul(m, axis_matrix(axis, angle[axis]))
    return m


def euler_xyz_to_matrix(pitch_deg, yaw_deg, roll_deg):
    """Rz(roll) @ Ry(yaw) @ Rx(pitch): extrinsic X, Y, Z = intrinsic Z, Y', X''. Locks at yaw = 90."""
    return euler_to_matrix(pitch_deg, yaw_deg, roll_deg, "ZYX")


def lock_rule(order):
    """(middle axis, outer axis, inner axis, sign) for M = R_outer R_middle R_inner.

    At middle = 90 deg, R_middle(90) sends the inner axis to sign * the outer axis, so
    R_middle(90) R_inner(c) = R_outer(sign * c) R_middle(90) and
    M = R_outer(a + sign * c) R_middle(90): only a + sign * c survives.
    """
    outer, middle, inner = order
    image = mat_vec(axis_matrix(middle, 90.0), AXES[inner])
    sign = round(sum(i * o for i, o in zip(image, AXES[outer])))
    return middle, outer, inner, sign


def gimbal_lock_demo(order="ZYX", pairs=((20.0, 10.0), (15.0, 5.0), (10.0, 0.0))):
    """Max matrix difference to the first pair for (outer, inner) angle pairs at middle = 90.

    The pairs must keep outer + sign * inner fixed (lock_rule); for the default order
    ZYX that is roll - pitch, so pairs are given as (pitch, roll) = (inner, outer).
    """
    middle, outer, inner, sign = lock_rule(order)

    def m(inner_deg, outer_deg):
        angle = {middle: 90.0, inner: inner_deg, outer: outer_deg}
        return euler_to_matrix(angle["X"], angle["Y"], angle["Z"], order)

    ref = m(*pairs[0])
    return tuple(mat_max_diff(ref, m(*p)) for p in pairs[1:])


def running_example_slerp():
    """Module 4 example E4: 40% of the way from identity to a 90 deg yaw about +y."""
    return slerp(IDENTITY, quat_from_axis_angle((0, 1, 0), 90.0), 0.4)


if __name__ == "__main__":
    q = running_example_slerp()
    print(f"slerp(identity, yaw90, t=0.4) = ({q[0]:.4f}, {q[1]:.4f}, {q[2]:.4f}, {q[3]:.4f})")
    axis, angle = quat_to_axis_angle(q)
    print(f"  -> axis {tuple(round(c, 3) for c in axis)}, angle {angle:.2f} deg (expect 36.00 deg = 0.4 x 90)")

    d12, d13 = gimbal_lock_demo()
    print(f"gimbal lock: max|M(20,90,10) - M(15,90,5)| = {d12:.2e}")
    print(f"gimbal lock: max|M(20,90,10) - M(10,90,0)| = {d13:.2e}")
    print("  -> both ~0 (not bit-identical, rounding only): at yaw=90 only roll - pitch is visible")
    for order in ("ZYX", "XZY", "YXZ"):
        middle, outer, inner, sign = lock_rule(order)
        combo = f"{ANGLE_NAME[outer]} {'+' if sign > 0 else '-'} {ANGLE_NAME[inner]}"
        print(f"order {order}: locks at {ANGLE_NAME[middle]} = 90, only {combo} survives")
