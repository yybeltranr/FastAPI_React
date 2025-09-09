import PropTypes from 'prop-types';
import "./ModalComponent.css";

const ModalComponent = ({ show, handleClose, titulo, bodyMessage, customButton, dialogClass = '', showFooter = true  }) => {
  const modalStyle = show ? { display: 'block', backgroundColor: 'rgba(0, 0, 0, 0.5)', zIndex: 10051 } : { display: 'none' };

  return (
    <div className="modal" style={modalStyle}>
      <div className={`modal-dialog modal-dialog-centered modal-dialog-scrollable ${dialogClass}`}>
        <div className="modal-content border-0 modalCard">
          <div className="modal-header tituloModal">
            <h5 className="modal-title">
                <strong>{titulo}</strong>{" "}
            </h5>
            <button type="button" className="btn-close" onClick={handleClose}></button>
          </div>
          <div className="modal-body m-0 p-0">
            {bodyMessage}
          </div>
          {showFooter && (
            <div className="modal-footer d-flex justify-content-evenly">
              {customButton && customButton}
              <button type="button" className="btn buttonsClose" onClick={handleClose}>
                Cancelar
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

ModalComponent.propTypes = {
  show: PropTypes.bool.isRequired,
  handleClose: PropTypes.func.isRequired,
  titulo: PropTypes.oneOfType([PropTypes.string, PropTypes.node]),
  bodyMessage: PropTypes.node,
  customButton: PropTypes.node,
  dialogClass: PropTypes.string,
  showFooter: PropTypes.bool
};

export default ModalComponent;