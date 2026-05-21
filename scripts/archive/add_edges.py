import json

with open(r"D:\Git_Repository\Mathemist\knowledge_graph.json", "r", encoding="utf-8") as f:
    data = json.load(f)

new_edges = [
    ("algebra_basic", "set_theory"),
    ("set_theory", "set_concept"),
    ("set_theory", "set_relations"),
    ("algebra_basic", "inequality"),
    ("inequality", "inequality_basic"),
    ("inequality", "quadratic_inequality"),
    ("inequality", "fraction_inequality"),
    ("algebra_basic", "basic_logic"),
    ("basic_logic", "proposition"),
    ("basic_logic", "conditions"),
    ("basic_logic", "logic_quantifiers"),
    ("analytic_geometry", "line_equation"),
    ("line_equation", "line_slope"),
    ("line_equation", "line_forms"),
    ("line_equation", "line_position"),
    ("analytic_geometry", "circle_equation"),
    ("circle_equation", "circle_standard"),
    ("circle_equation", "circle_line"),
    ("analytic_geometry", "conic_sections"),
    ("conic_sections", "ellipse"),
    ("conic_sections", "hyperbola"),
    ("conic_sections", "parabola"),
    ("conic_sections", "conic_applications"),
    ("analytic_geometry", "parametric_equation"),
    ("parametric_equation", "line_parametric"),
    ("parametric_equation", "conic_parametric"),
    ("analytic_geometry", "polar_coordinates"),
    ("polar_coordinates", "polar_basic"),
    ("sequence", "sequence_concept"),
    ("sequence_concept", "sequence_definition"),
    ("sequence", "arithmetic_sequence"),
    ("arithmetic_sequence", "arithmetic_definition"),
    ("arithmetic_sequence", "arithmetic_sum"),
    ("sequence", "geometric_sequence"),
    ("geometric_sequence", "geometric_definition"),
    ("geometric_sequence", "geometric_sum"),
    ("sequence", "sequence_applications"),
    ("sequence_applications", "sequence_recursion"),
    ("sequence_applications", "sequence_inequality"),
    ("sequence_applications", "sequence_model"),
    ("plane_vector", "vector_basic"),
    ("vector_basic", "vector_definition"),
    ("vector_basic", "vector_linear"),
    ("plane_vector", "vector_coordinate"),
    ("vector_coordinate", "vector_coordinate_ops"),
    ("vector_coordinate", "vector_dot_product"),
    ("plane_vector", "vector_applications_plane"),
    ("vector_applications_plane", "vector_geometry_app"),
    ("plane_geometry", "triangle_basic"),
    ("triangle_basic", "triangle_similarity"),
    ("triangle_basic", "triangle_congruence"),
    ("plane_geometry", "circle_basic_geometry"),
    ("circle_basic_geometry", "circle_theorems"),
    ("elementary_functions", "trigonometric_function"),
    ("trigonometric_function", "trig_definition"),
    ("trigonometric_function", "trig_graph_properties"),
    ("trigonometric_function", "trig_identity_relations"),
    ("trigonometric_function", "induction_formula"),
    ("trigonometric_function", "trig_identity_transformation"),
    ("trigonometric_function", "solve_triangle"),
    ("trig_identity_transformation", "double_angle"),
    ("trig_identity_transformation", "half_angle"),
    ("trig_identity_transformation", "sum_difference_formula"),
    ("trig_identity_transformation", "sum_to_product"),
    ("trig_identity_transformation", "auxiliary_angle"),
]

existing = set()
for e in data["edges"]:
    existing.add((e["source"], e["target"]))

added = 0
for s, t in new_edges:
    if (s, t) not in existing:
        data["edges"].append({"source": s, "target": t, "type": "包含"})
        existing.add((s, t))
        added += 1

with open(r"D:\Git_Repository\Mathemist\knowledge_graph.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"新增 {added} 条边，现有 {len(data['edges'])} 条边")
