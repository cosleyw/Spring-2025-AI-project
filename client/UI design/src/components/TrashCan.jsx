import { Droppable } from '@hello-pangea/dnd';
import './TrashCan.css';

export default function TrashCan() {
  return (
    <Droppable droppableId="trash" isDropDisabled={false}>
      {(provided) => (
        <div className="trashcan-outer" ref={provided.innerRef} {...provided.droppableProps}>
          <div className="trashcan-inner">
            <span>
              Block Course 🗑️<i style={{ opacity: '75%' }}>Drop here</i>
            </span>
            {provided.placeholder}
          </div>
        </div>
      )}
    </Droppable>
  );
}
