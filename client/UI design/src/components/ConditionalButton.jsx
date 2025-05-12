function ConditionalButton({ condition, onClick, children, className }) {
  return (
    <>
      {condition ? (
        <button className={className} onClick={onClick}>
          {children}
        </button>
      ) : (
        <div />
      )}
    </>
  );
}

export default ConditionalButton;
