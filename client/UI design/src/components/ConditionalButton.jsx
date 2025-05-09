function ConditionalButton({ condition, onClick, children }) {
  return <>{condition ? <button onClick={onClick}>{children}</button> : <div />}</>;
}

export default ConditionalButton;
