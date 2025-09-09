import { useState } from "react";
import bancos from "../data/bancos";
import ModalComponent from "../components/ModalComponent";
import { BsEyeFill, BsEyeSlashFill, BsLockFill } from "react-icons/bs";
import './Home.css'

function Home() {
  const [seleccionados, setSeleccionados] = useState([]);
  const [archivos, setArchivos] = useState({});
  const [showModal, setShowModal] = useState(false);
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const togglePasswordVisibility = () => setShowPassword(!showPassword);

  const closeModal = () => {
    setPassword("");
    setShowModal(false);
  };

  const toggleBanco = (banco) => {
    if (seleccionados.some((b) => b.id === banco.id)) {
      // Quitar banco -> borrar también archivos asociados
      setSeleccionados(seleccionados.filter((b) => b.id !== banco.id));
      setArchivos((prev) => {
        const nuevo = { ...prev };
        delete nuevo[banco.id];
        return nuevo;
      });
    } else {
      // Agregar banco
      setSeleccionados([...seleccionados, banco]);
    }
  };

  // Habilitar botón solo si todos los bancos seleccionados tienen al menos 1 archivo
  const handleArchivos = (bancoId, files) => {
    setArchivos((prev) => ({
      ...prev,
      [bancoId]: Array.from(files),
    }));
  };

  const botonHabilitado =
    seleccionados.length > 0 &&
    seleccionados.every((b) => archivos[b.id] && archivos[b.id].length > 0);

  return (  
    <div className="general-content">
      <div className="card cardPpal">
        <h4 className="card-header cardHeader">Automatización de informes</h4>
        <div className="card-body cardBodyPpal">
          <p className="card-text text-justify">
            Crea tus informes SIVICOF de forma rápida y sencilla.
            Simplemente <strong> selecciona</strong> los bancos,
            <strong> carga</strong> los archivos PDF y nuestro sistema
            se encarga del resto.
            <strong> Extraemos</strong> la información clave por ti;
            solo tendrás que verificar y completar algunos datos antes de 
            <strong> descargar</strong> el informe final en formato Excel.
          </p>
          <br />
          <p className='text-center fst-italic fs-5'>
            Automatiza tus tareas repetitivas y gana tiempo para lo que realmente importa.
          </p>
          <br />
        </div>
      </div>
      <div className="card cardSeleccion text-start">
        <div className="card-body cardBodySeleccion">
          <p className="fw-bold">
            Seleciona los bancos que deseas incluir en el informe:
          </p>
          <div className="row">
            {bancos.map((banco) => (
              <div className="col-md-4" key={banco.id}>
                <div className="form-check">
                  <input
                    type="checkbox"
                    className="form-check-input"
                    id={banco.id}
                    checked={seleccionados.some((b) => b.id === banco.id)}
                    onChange={() => toggleBanco(banco)}
                  />
                  <label className="form-check-label" htmlFor={banco.id}>
                    {banco.nombre}
                  </label>
                </div>
              </div>
            ))}
          </div>

          <hr />

          <div className="row">
            {seleccionados.map((banco) => (
              <div className="col-md-12 col-lg-6 col-xl-3 mb-3" key={banco.id}>
                <div className="card cardBanks h-100">
                  <div className="card-body">
                    <h5 className="card-title fst-italic fw-medium">{banco.nombre}</h5>
                    <p className="card-text">
                      Selecciona los PDFs correspondientes a <b>{banco.nombre}</b> para procesar:
                    </p>
                    <input 
                      type="file" 
                      multiple 
                      accept="application/pdf" 
                      className="form-control"
                      onChange={(e) =>
                        handleArchivos(banco.id, e.target.files)
                      }
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <hr />

          <p className="text-muted fst-italic" style={{fontSize: '0.9em'}}>
            <b>Nota: </b>El botón para procesar los PDFs solo se activará una vez hayas seleccionado al 
            menos un archivo por cada banco elegido. Si no seleccionas ningún banco, el botón 
            permanecerá deshabilitado. Si no tienes archivos para alguno de los bancos seleccionados,
            por favor, deselecciónalo antes de proceder.
          </p>

          <div className="d-flex justify-content-center align-items-center flex-column"> 
            <button 
              type="submit" 
              className="btn buttons text-center m-4" 
              style={{width: '40%'}} 
              disabled={!botonHabilitado}
              
              onClick={() => setShowModal(true)}
            >
              Procesar todos los archivos
            </button>

            <ModalComponent 
              show={showModal}
              handleClose={closeModal}
              titulo="Password"
              bodyMessage={
                <div className='container-fluid text-center p-4'>
                  Uno o varios archivos PDF pueden requerir una contraseña para abrirse.
                  <br />
                  Por favor, ingresa la contraseña a continuación:
                  <div className="mb-3 position-relative">
                    <div className="input-icon">
                      <i className="bi bi-lock">
                        <BsLockFill />
                      </i>
                      <i
                        className="toggle-password-icon seePassw"
                        onClick={togglePasswordVisibility}
                      >
                        {showPassword ? <BsEyeFill /> : <BsEyeSlashFill />}
                      </i>
                      <input 
                        type={showPassword ? "text" : "password"}
                        className="form-control custom-input mt-3" 
                        id="password"
                        value={password}
                        onChange={(e) => {
                          const value = e.target.value.replace(/[^0-9]/g, "");
                          setPassword(value);
                        }}
                      />
                    </div>
                    <button 
                      type="submit" 
                      className="btn buttons text-center mt-4" 
                      style={{width: '40%'}}
                    >
                      Continuar
                    </button>
                  </div>
                </div>
              }
              customButton={''}
              dialogClass="modal-md"
              showFooter = {false}
            />

            <div className="accordion" id="accordionPanelsBanks">
              <div className="accordion-item">
                <h2 className="accordion-header">
                  <button className="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#panelsStayOpen-collapseOne" aria-expanded="true" aria-controls="panelsStayOpen-collapseOne">
                    Accordion Item #1
                  </button>
                </h2>
                <div id="panelsStayOpen-collapseOne" className="accordion-collapse collapse show">
                  <div className="accordion-body">
                    <strong>This is the first item’s accordion body.</strong> It is shown by default, until the collapse plugin adds 
                    the appropriate classes that we use to style each element. These classes control the overall appearance, as well 
                    as the showing and hiding via CSS transitions. You can modify any of this with custom CSS or overriding our default 
                    variables. It’s also worth noting that just about any HTML can go within the <code>.accordion-body</code>, though the transition does limit overflow.
                  </div>
                </div>
              </div>
            </div>
          </div>   
            
          
        </div>
      </div>
    </div>  
  )
}

export default Home