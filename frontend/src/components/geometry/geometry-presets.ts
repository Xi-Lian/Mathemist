export type GeometryMode = "2d" | "3d";

export interface GeometryPreset {
  label: string;
  commands: string[];
}

export interface GeometrySection {
  title: string;
  presets: GeometryPreset[];
}

export const PRESETS_2D: GeometrySection[] = [
  {
    title: "平面图形",
    presets: [
      {
        label: "等边三角形",
        commands: ["A=(0,0)", "B=(2,0)", "C=(1,1.732)", "Polygon(A,B,C)"],
      },
      {
        label: "等腰三角形",
        commands: ["A=(0,0)", "B=(3,0)", "C=(1.5,2)", "Polygon(A,B,C)"],
      },
      {
        label: "直角三角形",
        commands: ["A=(0,0)", "B=(3,0)", "C=(0,2)", "Polygon(A,B,C)"],
      },
      {
        label: "正方形",
        commands: [
          "A=(0,0)",
          "B=(2,0)",
          "C=(2,2)",
          "D=(0,2)",
          "Polygon(A,B,C,D)",
        ],
      },
      {
        label: "长方形",
        commands: [
          "A=(0,0)",
          "B=(3,0)",
          "C=(3,2)",
          "D=(0,2)",
          "Polygon(A,B,C,D)",
        ],
      },
      {
        label: "平行四边形",
        commands: [
          "A=(0,0)",
          "B=(3,0)",
          "C=(4,2)",
          "D=(1,2)",
          "Polygon(A,B,C,D)",
        ],
      },
      {
        label: "菱形",
        commands: [
          "A=(1,0)",
          "B=(3,1.732)",
          "C=(1,3.464)",
          "D=(-1,1.732)",
          "Polygon(A,B,C,D)",
        ],
      },
      {
        label: "梯形",
        commands: [
          "A=(0,0)",
          "B=(4,0)",
          "C=(3,2)",
          "D=(1,2)",
          "Polygon(A,B,C,D)",
        ],
      },
      {
        label: "圆形",
        commands: ["O=(0,0)", "Circle(O,2)"],
      },
      {
        label: "椭圆",
        commands: ["F1=(-2,0)", "F2=(2,0)", "P=(0,1.5)", "Ellipse(F1, F2, P)"],
      },
      {
        label: "正五边形",
        commands: [
          "A=(2,0)",
          "B=(0.618,1.902)",
          "C=(-1.618,1.176)",
          "D=(-1.618,-1.176)",
          "E=(0.618,-1.902)",
          "Polygon(A,B,C,D,E)",
        ],
      },
      {
        label: "正六边形",
        commands: [
          "A=(2,0)",
          "B=(1,1.732)",
          "C=(-1,1.732)",
          "D=(-2,0)",
          "E=(-1,-1.732)",
          "F=(1,-1.732)",
          "Polygon(A,B,C,D,E,F)",
        ],
      },
    ],
  },
  {
    title: "函数图像",
    presets: [
      { label: "一次函数: y = x", commands: ["f(x) = x"] },
      { label: "一次函数: y = 2x + 1", commands: ["f(x) = 2x + 1"] },
      { label: "二次函数: y = x²", commands: ["f(x) = x^2"] },
      { label: "二次函数: y = -x² + 2x + 3", commands: ["f(x) = -x^2 + 2x + 3"] },
      { label: "三次函数: y = x³", commands: ["f(x) = x^3"] },
      { label: "反比例函数: y = 1/x", commands: ["f(x) = 1/x"] },
      { label: "指数函数: y = 2^x", commands: ["f(x) = 2^x"] },
      { label: "对数函数: y = ln(x)", commands: ["f(x) = ln(x)"] },
      { label: "正弦函数: y = sin(x)", commands: ["f(x) = sin(x)"] },
      { label: "余弦函数: y = cos(x)", commands: ["f(x) = cos(x)"] },
      { label: "正切函数: y = tan(x)", commands: ["f(x) = tan(x)"] },
    ],
  },
];

export const PRESETS_3D: GeometrySection[] = [
  {
    title: "立体图形",
    presets: [
      { label: "球体", commands: ["O=(0,0,0)", "Sphere(O,2)"] },
      {
        label: "正方体",
        commands: [
          "A=(0,0,0)",
          "B=(2,0,0)",
          "C=(2,2,0)",
          "D=(0,2,0)",
          "E=(0,0,2)",
          "F=(2,0,2)",
          "G=(2,2,2)",
          "H=(0,2,2)",
          "Polygon(A,B,C,D)",
          "Polygon(E,F,G,H)",
          "Polygon(A,B,F,E)",
          "Polygon(B,C,G,F)",
          "Polygon(C,D,H,G)",
          "Polygon(D,A,E,H)",
        ],
      },
      {
        label: "长方体",
        commands: [
          "A=(0,0,0)",
          "B=(3,0,0)",
          "C=(3,2,0)",
          "D=(0,2,0)",
          "E=(0,0,1.5)",
          "F=(3,0,1.5)",
          "G=(3,2,1.5)",
          "H=(0,2,1.5)",
          "Polygon(A,B,C,D)",
          "Polygon(E,F,G,H)",
          "Polygon(A,B,F,E)",
          "Polygon(B,C,G,F)",
          "Polygon(C,D,H,G)",
          "Polygon(D,A,E,H)",
        ],
      },
      { label: "圆柱", commands: ["O1=(0,0,0)", "O2=(0,0,3)", "Cylinder(O1, O2, 1.5)"] },
      { label: "圆锥", commands: ["O=(0,0,0)", "P=(0,0,3)", "Cone(O, P, 1.5)"] },
      {
        label: "四面体",
        commands: [
          "A=(0,0,0)",
          "B=(2,0,0)",
          "C=(1,1.732,0)",
          "D=(1,0.577,1.633)",
          "Polygon(A,B,C)",
          "Polygon(A,B,D)",
          "Polygon(B,C,D)",
          "Polygon(C,A,D)",
        ],
      },
      {
        label: "三棱柱",
        commands: [
          "A=(0,0,0)",
          "B=(2,0,0)",
          "C=(1,1.732,0)",
          "A1=(0,0,2)",
          "B1=(2,0,2)",
          "C1=(1,1.732,2)",
          "Polygon(A,B,C)",
          "Polygon(A1,B1,C1)",
          "Polygon(A,B,B1,A1)",
          "Polygon(B,C,C1,B1)",
          "Polygon(C,A,A1,C1)",
        ],
      },
      {
        label: "四棱锥",
        commands: [
          "A=(0,0,0)",
          "B=(2,0,0)",
          "C=(2,2,0)",
          "D=(0,2,0)",
          "P=(1,1,2.5)",
          "Polygon(A,B,C,D)",
          "Polygon(A,B,P)",
          "Polygon(B,C,P)",
          "Polygon(C,D,P)",
          "Polygon(D,A,P)",
        ],
      },
      {
        label: "正八面体",
        commands: [
          "A=(1.414,0,0)",
          "B=(-1.414,0,0)",
          "C=(0,1.414,0)",
          "D=(0,-1.414,0)",
          "E=(0,0,1.414)",
          "F=(0,0,-1.414)",
          "Polygon(A,C,E)",
          "Polygon(C,B,E)",
          "Polygon(B,D,E)",
          "Polygon(D,A,E)",
          "Polygon(A,C,F)",
          "Polygon(C,B,F)",
          "Polygon(B,D,F)",
          "Polygon(D,A,F)",
        ],
      },
    ],
  },
];
