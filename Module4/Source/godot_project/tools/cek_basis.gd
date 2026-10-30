extends SceneTree
## Prints the Basis Godot builds from Euler angles, for docs/catatan/fase5-godot-scene.md (T4).
## Run: $GODOT --headless --path godot_project --script res://tools/cek_basis.gd
## Each line: case, rotation_order, pitch/yaw/roll in degrees, then the 3 x 3 matrix row by row
## (row i, column j = basis[j][i], because Basis.x/y/z are the columns).

const CASES := [
	["yaw90_beda10", Vector3(20, 90, 10)], ["yaw90_beda10", Vector3(15, 90, 5)], ["yaw90_beda10", Vector3(10, 90, 0)],
	["pitch90_yawminroll", Vector3(90, 20, 10)], ["pitch90_yawminroll", Vector3(90, 15, 5)],
	["pitch90_yawminroll", Vector3(90, 10, 0)],
	["acak", Vector3(20, 30, 40)], ["acak", Vector3(-35, 70, 125)],
]


func _init() -> void:
	var node := Node3D.new()
	print("CEK rotation_order_default=%d EULER_ORDER_YXZ=%d EULER_ORDER_ZYX=%d" % [
		node.rotation_order, EULER_ORDER_YXZ, EULER_ORDER_ZYX])
	for order in [EULER_ORDER_YXZ, EULER_ORDER_ZYX]:
		node.rotation_order = order
		for c in CASES:
			var deg: Vector3 = c[1]
			node.rotation = Vector3(deg_to_rad(deg.x), deg_to_rad(deg.y), deg_to_rad(deg.z))
			var b := node.basis
			var rows := []
			for i in 3:
				for j in 3:
					rows.append("%.9f" % b[j][i])
			print("BASIS %s order=%d deg=%s,%s,%s m=%s" % [c[0], order, deg.x, deg.y, deg.z, ",".join(rows)])
	node.free()
	quit()
