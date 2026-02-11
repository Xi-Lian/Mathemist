export function LangGraphLogoSVG({
  className,
  width,
  height,
}: {
  width?: number;
  height?: number;
  className?: string;
}) {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* 开放三角形 + 斜线 */}
      <g fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="butt" strokeLinejoin="miter">
        {/* 开放三角形 */}
        <path d="M25 75 L50 25 L75 75" />
        {/* 极简斜线切入 */}
        <line x1="15" y1="60" x2="85" y2="40" />
      </g>
    </svg>
  );
}

export function MathemistLogoWithText({
  className,
  width,
  height,
}: {
  width?: number;
  height?: number;
  className?: string;
}) {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 220 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* 几何图形 Logo - 48x48 区域，更大更醒目 */}
      <g transform="translate(0, 0)" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="butt" strokeLinejoin="miter">
        {/* 开放三角形 - 放大版 */}
        <path d="M12 36 L24 8 L36 36" />
        {/* 极简斜线切入 - 更有力 */}
        <line x1="6" y1="28" x2="42" y2="18" />
      </g>
      {/* Mathemist 文字 - 普通英文字体 */}
      <text
        x="56"
        y="50%"
        dominantBaseline="middle"
        fill="currentColor"
        style={{
          fontFamily: 'Inter, system-ui, sans-serif',
          fontSize: '30px',
          fontWeight: 600,
          letterSpacing: '0.02em',
        }}
      >
        Mathemist
      </text>
    </svg>
  );
}
