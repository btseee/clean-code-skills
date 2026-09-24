type BadgeProps = {
  color: "blue" | "green" | "red";
  children: React.ReactNode;
};

export function Badge({ color, children }: BadgeProps) {
  return (
    <span className={`bg-${color}-500 text-white px-2 py-1 rounded`}>
      {children}
    </span>
  );
}
