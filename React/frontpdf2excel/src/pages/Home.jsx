import { useEffect, useState } from "react"; 
import { useForm, Controller } from "react-hook-form";
import Swal from "sweetalert2";
import { bancosFiltrados, tiposCaja, tiposCuenta, monedas, utilizaciones } from "../data/listas";
import ModalComponent from "../components/ModalComponent";
import { BsEyeFill, BsEyeSlashFill, BsLockFill } from "react-icons/bs";
import { API_BASE_URL } from "../apiConfig";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import './Home.css';

function Home() {
  const { control, getValues } = useForm({
    defaultValues: {
      camposArchivos: {},
      responsableCargo: "Gerencia General / Carlos Felipe Reyes Forero\nSubgerencia Corporativa / Javier Antonio Villarreal Villaquiran\nTesorera General / Irene Duarte Méndez",
      poliza: "Poliza 930-64-994000000201 - 930-63-994000000156\nAseguradora Solidaria de Colombia",
      fechaConciliacion: null
    }
  });

  const [seleccionados, setSeleccionados] = useState([]);
  const [archivos, setArchivos] = useState({});
  //const [showModal, setShowModal] = useState(false);
  const [excelListo, setExcelListo] = useState(false);
  const [showModalGenerar, setShowModalGenerar] = useState(false);
  //const [password, setPassword] = useState("");
  //const [showPassword, setShowPassword] = useState(false);
  const [resultados, setResultados] = useState({});
  const [procesando, setProcesando] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [valores, setValores] = useState({});
  const [isEditingExcel, setIsEditingExcel] = useState(false);
  const [fechaCierre, setFechaCierre] = useState(null);
  const [fechaConciliacion, setFechaConciliacion] = useState(null);
  const [responsableCargo, setResponsableCargo] = useState("");
  const [poliza, setPoliza] = useState("");

  useEffect(() => {
    setResponsableCargo(getValues("responsableCargo"));
    setPoliza(getValues("poliza"));
  }, [getValues]);

  useEffect(() => {
    const nuevosValores = {};
    Object.entries(resultados).forEach(([banco, archivos]) => {
      archivos.forEach((archivo, archivoIndex) => {
        const keyArchivo = `${banco}-${archivoIndex}`;
        if (!valores[keyArchivo]) {
          const rawNumero = archivo.resultado?.texto?.["NÚMERO"] ?? archivo.resultado?.texto?.["NUMERO"] ?? "";
          const cleanNumero = rawNumero.toString().replace(/\D/g, "");
          const found = findUtilizacionByNumero(cleanNumero, utilizaciones);
          const utilizacion = found?.u;
          nuevosValores[keyArchivo] = {
            subcuenta: { id: 3, nombre: tiposCaja.find(c => c.id === 3)?.nombre || "" },
            moneda: { id: 1, nombre: monedas.find(m => m.id === 1)?.nombre || "" },
            utilizacionTexto: utilizacion ? utilizacion.nombre : cleanNumero,
            tasa: "",
            fecha: utilizacion ? utilizacion.fecha : "",
            observaciones: "",
            fechaCierre: ""
          };
        }
      });
    });
    setValores(prev => ({ ...prev, ...nuevosValores }));
  }, [resultados]);

  //const togglePasswordVisibility = () => setShowPassword(!showPassword);

  //const closeModal = () => {
  //  setPassword("");
  //  setShowModal(false);
  //};

  const closeModalGenerar = () => setShowModalGenerar(false);

  const toggleBanco = (banco) => {
    if (seleccionados.some((b) => b.id === banco.id)) {
      setSeleccionados(seleccionados.filter((b) => b.id !== banco.id));
      setArchivos((prev) => {
        const nuevo = { ...prev };
        delete nuevo[banco.id];
        return nuevo;
      });
    } else {
      setSeleccionados([...seleccionados, banco]);
    }
  };

  const handleArchivos = (bancoId, files) => {
    setArchivos((prev) => ({
      ...prev,
      [bancoId]: Array.from(files),
    }));
  };

  const botonHabilitado = seleccionados.length > 0 && seleccionados.every((b) => archivos[b.id] && archivos[b.id].length > 0);

  const procesarArchivos = async () => {
    setProcesando(true);
    setExcelListo(false);
    const nuevosResultados = {};

    for (const banco of seleccionados) {
      nuevosResultados[banco.nombre] = [];

      for (const file of archivos[banco.id] || []) {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("banco", banco.nombre);

        const response = await fetch(`${API_BASE_URL}/pdf/procesar`, {
          method: "POST",
          body: formData,
        });
        
        const data = await response.json();
        nuevosResultados[banco.nombre].push({
          nombreArchivo: file.name,
          resultado: data,
        });
      }
    }

    setResultados(nuevosResultados);
    setProcesando(false);
    setExcelListo(true);
  };

  function findUtilizacionByNumero(num, utilizaciones) {
    if (!num) return undefined;
    const cleanNum = num.toString().replace(/\D/g, "");

    for (const u of utilizaciones) {
      const idClean = u.id.toString().replace(/\D/g, "");
      if (cleanNum === idClean) return { u, match: "exact" };
    }

    for (const u of utilizaciones) {
      const idClean = u.id.toString().replace(/\D/g, "");
      if (cleanNum.endsWith(idClean)) return { u, match: "endsWith" };
    }

    for (const u of utilizaciones) {
      const idClean = u.id.toString().replace(/\D/g, "");
      if (cleanNum.includes(idClean)) return { u, match: "includes" };
    }

    const maxK = Math.min(12, cleanNum.length);
    for (let k = maxK; k >= 4; k--) {
      for (const u of utilizaciones) {
        const idClean = u.id.toString().replace(/\D/g, "");
        if (!idClean || idClean.length < k) continue;
        if (cleanNum.slice(-k) === idClean.slice(-k)) {
          return { u, match: `suffix-${k}` };
        }
      }
    }
    return undefined;
  }

  const actualizar = (keyArchivo, campo, valor) => {
    // Mapeo de campos que requieren id + nombre
    const listasMap = {
      subcuenta: tiposCaja,
      moneda: monedas,
      tipoCuenta: tiposCuenta,
      banco: bancosFiltrados
    };

    let nuevoValor = valor;

    if (listasMap[campo]) {
      const lista = listasMap[campo];
      const encontrado = lista.find(item => item.id === valor);
      nuevoValor = encontrado ? { id: encontrado.id, nombre: encontrado.nombre } : { id: valor, nombre: "" };
    }

    setValores(prev => ({
      ...prev,
      [keyArchivo]: {
        ...prev[keyArchivo],
        [campo]: nuevoValor ?? "",
      }
    }));
  };

  const validarCampos = () => {
    for (const valoresArchivo of Object.values(valores)) {
      if (!valoresArchivo.subcuenta && valoresArchivo.subcuenta !== 0) return false;
      if (!valoresArchivo.moneda && valoresArchivo.moneda !== 0) return false;
      if (!valoresArchivo.utilizacionTexto || valoresArchivo.utilizacionTexto.trim() === "") return false;
      if (!valoresArchivo.tasa || valoresArchivo.tasa === "") return false;
      if (!valoresArchivo.fecha || valoresArchivo.fecha.trim() === "") return false;
    }
    return true;
  };

  const handleGenerarExcel = () => {
    if (!validarCampos()) {
      Swal.fire({
        icon: "warning",
        title: "Campos incompletos",
        text: "Por favor, complete todos los campos obligatorios * antes de generar el informe. Las observaciones son opcionales.",
        confirmButtonText: "Aceptar",
        confirmButtonColor: "#00C29D",
        customClass: {
          confirmButton: "swal-confirm-btn"
        }
      });
      return;
    }
    setShowModalGenerar(true);
  };

  const toggleEdit = () => setIsEditingExcel(!isEditingExcel);

  const descargarExcel = async () => {
    try {
      const valoresParaEnviar = JSON.parse(JSON.stringify(valores));
      const payload = {
        fechaCierre,
        fechaConciliacion,
        responsableCargo,
        poliza,
        resultados,
        valores_frontend: valoresParaEnviar
      }; 
      
      const response = await fetch(`${API_BASE_URL}/pdf/exportar-excel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error("Error al generar el Excel");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      const fechaStr = fechaConciliacion 
        ? fechaConciliacion.toLocaleDateString("es-CO").replace(/\//g, "_")
        : "";
      link.href = url;
      link.setAttribute("download", `Informe_SIVICOF_${fechaStr}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      closeModalGenerar();
      Swal.fire({
        icon: 'success',
        title: 'Éxito',
        text: 'El informe en Excel se ha generado y descargado correctamente.',
        confirmButtonText: 'Aceptar',
        confirmButtonColor: '#00C29D',
        customClass: {
          confirmButton: 'swal-confirm-btn'
        }
      });
    } catch (error) {
      console.error("Error descargando el Excel:", error);
      Swal.fire({
        icon: 'error',
        title: 'Error',
        text: 'No se pudo generar el Excel. Intenta nuevamente.',
        confirmButtonText: 'Aceptar',
        confirmButtonColor: '#00C29D',
        customClass: {
          confirmButton: 'swal-confirm-btn'
        }
      });
    }
  };

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

      {/* Selección de bancos */}
      <div className="card cardSeleccion text-start">
        <div className="card-body cardBodySeleccion">
          <p className="fw-bold">Selecciona los bancos que deseas incluir en el informe:</p>
          <div className="row">
            {bancosFiltrados.map((banco) => (
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

          {/* Archivos por banco */}
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
                      onChange={(e) => handleArchivos(banco.id, e.target.files)}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <hr />
          <p className="text-muted fst-italic" style={{ fontSize: '0.9em' }}>
            <b>Nota: </b>El botón para procesar los PDFs solo se activará una vez hayas seleccionado al 
            menos un archivo por cada banco elegido.
          </p>

          <div className="d-flex justify-content-center align-items-center flex-column"> 
            <button 
              type="button" 
              className="btn buttons text-center m-4" 
              style={{width: '40%'}} 
              disabled={!botonHabilitado}
              /* onClick={() => setShowModal(true)} */
              onClick={procesarArchivos}
            >
              Procesar todos los archivos
            </button>
          </div>   

          {procesando && (
            <div className="text-center my-4">
              <div className="spinner-border text-secondary" role="status">
                <span className="visually-hidden">Procesando...</span>
              </div>
              <p className="mt-3 fw-bold">Procesando archivos, por favor espera...</p>
            </div>
          )}

          {/* Resultados */}
          <div className="accordion mt-3" id="resultadosAccordion">
            {Object.entries(resultados).map(([banco, archivos], bancoIndex) => (
              <div className="accordion-item" key={bancoIndex}>
                <h2 className="accordion-header" id={`heading-${bancoIndex}`}>
                  <button
                    className="accordion-button collapsed fw-bold"
                    type="button"
                    data-bs-toggle="collapse"
                    data-bs-target={`#collapse-${bancoIndex}`}
                    aria-expanded="false"
                    aria-controls={`collapse-${bancoIndex}`}
                  >
                    {banco}
                  </button>
                </h2>

                <div
                  id={`collapse-${bancoIndex}`}
                  className="accordion-collapse collapse"
                  aria-labelledby={`heading-${bancoIndex}`}
                  data-bs-parent="#resultadosAccordion"
                >
                  <div className="accordion-body">
                    {archivos.map((archivo, archivoIndex) => {
                      const keyArchivo = `${banco}-${archivoIndex}`;
                      const valoresArchivo = valores[keyArchivo] || {
                        subcuenta: { id: 3, nombre: tiposCaja.find(c => c.id === 3)?.nombre || "" },
                        moneda: { id: 1, nombre: monedas.find(m => m.id === 1)?.nombre || "" },
                        utilizacionTexto: "",
                        tasa: "",
                        fecha: "",
                        observaciones: "",
                      };

                      return (
                        <div key={archivoIndex} className="mb-4">
                          <h5 className="fst-italic fw-medium">{archivo.nombreArchivo}</h5>

                          {/* Información del PDF */}
                          <ul className="list-group list-group-flush mb-3">
                            {archivo.resultado?.texto &&
                              Object.entries(archivo.resultado.texto).map(([key, value]) => (
                                <li key={key} className="list-group-item">
                                  <strong>{key}:</strong> {value}
                                </li>
                              ))}
                          </ul>

                          {/* Movimientos */}
                          <p className="fst-italic fw-medium">Movimientos del mes:</p>
                          <ul className="list-group list-group-flush">
                            {archivo.resultado?.tablas &&
                              Object.entries(archivo.resultado.tablas).map(([key, value]) => (
                                <li key={key} className="list-group-item">
                                  <strong>{key}:</strong> {value}
                                </li>
                              ))}
                            {archivo.resultado?.max_movimiento && (
                              <li className="list-group-item">
                                <strong>Movimiento mas grande del mes:</strong> {archivo.resultado.max_movimiento}
                              </li>
                            )}
                          </ul>

                          {/* Campos editables */}
                          <div className="mt-3">
                            <label className="form-label fst-italic fw-medium">* Subcuenta efectivo:</label>
                            <select
                              className="form-select mb-2"
                              disabled={!isEditing}
                              value={valoresArchivo.subcuenta?.id || ""}
                              onChange={(e) =>
                                actualizar(keyArchivo, "subcuenta", Number(e.target.value))
                              }
                            >
                              {tiposCaja.map(caja => (
                                <option key={caja.id} value={caja.id}>
                                  {caja.nombre}
                                </option>
                              ))}
                            </select>

                            <label className="form-label fst-italic fw-medium">* Moneda:</label>
                            <select
                              className="form-select mb-2"
                              disabled={!isEditing}
                              value={valoresArchivo.moneda?.id || ""}
                              onChange={(e) =>
                                actualizar(keyArchivo, "moneda", Number(e.target.value))
                              }
                            >
                              {monedas.map(moneda => (
                                <option key={moneda.id} value={moneda.id}>
                                  {moneda.nombre}
                                </option>
                              ))}
                            </select>

                            <label className="form-label fst-italic fw-medium">* Utilización:</label>
                            <textarea
                              className="form-control mb-2"
                              rows={2}
                              disabled={!isEditing}
                              value={valoresArchivo.utilizacionTexto}
                              onChange={(e) =>
                                actualizar(keyArchivo, "utilizacionTexto", e.target.value)
                              }
                            />

                            <label className="form-label fst-italic fw-medium">* Tasa de interés bancario:</label>
                            <input
                              type="number"
                              className="form-control mb-2"
                              placeholder="Ingrese la tasa (%)"
                              value={valoresArchivo.tasa}
                              min="0"
                              onChange={(e) => {
                                const value = e.target.value;
                                const regex = /^[0-9]*\.?[0-9]*$/;
                                if (regex.test(value)) {
                                  actualizar(keyArchivo, "tasa", value);
                                }
                              }}
                            />

                            <label className="form-label fst-italic fw-medium">* Fecha de constitución:</label>
                            <input
                              type="text"
                              className="form-control mb-2"
                              disabled={!isEditing}
                              value={valoresArchivo.fecha}
                              onChange={(e) =>
                                actualizar(keyArchivo, "fecha", e.target.value)
                              }
                            />

                            <label className="form-label fst-italic fw-medium">Observaciones:</label>
                            <textarea
                              className="form-control mb-2"
                              rows={2}
                              value={valoresArchivo.observaciones}
                              onChange={(e) =>
                                actualizar(keyArchivo, "observaciones", e.target.value)
                              }
                            />

                            <label htmlFor="fechaCierre" className="form-label fst-italic fw-medium me-4">
                              Fecha de cierre
                            </label>
                            <Controller
                              control={control}
                              name="fechaCierre"
                              render={({ field }) => (
                                <DatePicker
                                  className="form-control"
                                  selected={field.value}
                                  onChange={field.onChange}
                                  dateFormat="dd/MM/yyyy"
                                  placeholderText="Seleccione una fecha"
                                  showMonthDropdown
                                  showYearDropdown
                                  dropdownMode="select"
                                />
                              )}
                            />
                          </div>

                          <div className="d-flex justify-content-center">
                            <button
                              type="button"
                              className="btn buttonsInside m-4"
                              style={{ width: "30%" }}
                              onClick={() => setIsEditing(!isEditing)}
                            >
                              {isEditing ? "Guardar" : "Editar campos inhabilitados"}
                            </button>
                          </div>
                          
                          <hr />
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <hr />

        <div className="d-flex justify-content-center align-items-center flex-column m-4"> 
          <p className="text-muted fst-italic" style={{ fontSize: '0.9em' }}>
            <b>Nota: </b>El botón para generar el informe en Excel solo se activará una vez hayas rellenado 
            los campos obligatorios * de todos los archivos procesados. El campo Observaciones es opcional.
          </p>
          <button 
            type="button" 
            className="btn buttons text-center m-4" 
            style={{width: '40%'}} 
            disabled={!excelListo}
            onClick={handleGenerarExcel}
          >
            Generar informe en Excel
          </button>
        </div> 
      </div>

      {/* Modal Password */}
      {/* <ModalComponent 
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
                <i className="bi bi-lock"><BsLockFill /></i>
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
                  onChange={(e) => setPassword(e.target.value.replace(/[^0-9]/g, ""))}
                />
              </div>
              <button 
                type="button" 
                className="btn buttons text-center mt-4" 
                style={{width: '40%'}}
                disabled={!password}
                onClick={async () => {
                  closeModal();
                  setProcesando(true);
                  await procesarArchivos(); 
                  setProcesando(false);
                }}
              >
                Continuar
              </button>
            </div>
          </div>
        }
        customButton={''}
        dialogClass="modal-md"
        showFooter={false}
      /> */}

      {/* Modal Generar Excel */}
      <ModalComponent 
        show={showModalGenerar}
        handleClose={closeModalGenerar}
        titulo="Generando informe..."
        bodyMessage={
          <div className='container-fluid text-start p-4'>
            <label htmlFor="responsableCargo" className="form-label fst-italic fw-medium">
              Responsable / Cargo
            </label>
            <textarea
              id="responsableCargo"
              className="form-control mb-4"
              rows={3}
              disabled={!isEditingExcel}
              value={responsableCargo}
              onChange={(e) => setResponsableCargo(e.target.value)}
            />
            <label htmlFor="poliza" className="form-label fst-italic fw-medium">
              Póliza de manejo
            </label>
            <textarea
              id="poliza"
              className="form-control mb-4"
              rows={2}
              disabled={!isEditingExcel}
              value={poliza}
              onChange={(e) => setPoliza(e.target.value)}
            />
            <label htmlFor="fechaConciliacion" className="form-label fst-italic fw-medium  me-4">
              Fecha de conciliación
            </label>
            <Controller
              control={control}
              name="fechaConciliacion"
              render={({ field }) => (
                <DatePicker
                  className="form-control"
                  selected={fechaConciliacion}
                  onChange={(date) => { field.onChange(date); setFechaConciliacion(date); }}
                  dateFormat="dd/MM/yyyy"
                  placeholderText="Seleccione una fecha"
                  showMonthDropdown
                  showYearDropdown
                  dropdownMode="select"
                />
              )}
            />

            <div className="d-flex justify-content-center">
              <button
                type="button"
                className="btn buttonsInside m-4"
                style={{ width: "80%" }}
                onClick={toggleEdit}
              >
                {isEditingExcel ? "Guardar" : "Editar campos inhabilitados"}
              </button>
            </div>

            <hr />  
            <div className="d-flex justify-content-end mt-4"> 
              <button 
                type="button" 
                className="btn buttons text-center m-2" 
                style={{width: '40%'}} 
                disabled={!fechaConciliacion}
                onClick={descargarExcel}
              >
                Descargar Excel
              </button>
            </div> 
          </div>
        }
        customButton={''}
        dialogClass="modal-lg"
        showFooter={false}
      />
    </div>
  );
}

export default Home;