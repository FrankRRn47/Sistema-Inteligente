import { useCallback, useEffect, useRef, useState } from 'react';

import MediaResultCard from '../components/MediaResultCard.jsx';
import {
  analyzeImageUpload,
  analyzeVideoUpload,
  analyzeWebcamUpload,
  analyzeWebcamFrame,
  startLiveSession,
  stopLiveSession,
  fetchMediaHistory,
  fetchModelMetadata,
} from '../services/mediaService.js';

function MediaLab() {
    const [filterOpen, setFilterOpen] = useState(false);
  const [metadata, setMetadata] = useState(null);
  const [history, setHistory] = useState([]);
  const [latestResults, setLatestResults] = useState([]);
  const [availableEmotions, setAvailableEmotions] = useState([]);
  const [historyFilters, setHistoryFilters] = useState({ mediaType: 'image', emotion: 'all' });
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');

  const [imageFile, setImageFile] = useState(null);
  const [imageChannel, setImageChannel] = useState('manual');
  const [imageError, setImageError] = useState('');
  const [imageLoading, setImageLoading] = useState(false);

  const [videoFile, setVideoFile] = useState(null);
  const [videoChannel, setVideoChannel] = useState('manual');
  const [videoError, setVideoError] = useState('');
  const [videoLoading, setVideoLoading] = useState(false);

  const [webcamChannel, setWebcamChannel] = useState('webcam');
  const [webcamError, setWebcamError] = useState('');
  const [webcamLoading, setWebcamLoading] = useState(false);
  const [isPreviewActive, setIsPreviewActive] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingBlob, setRecordingBlob] = useState(null);
  const [isLiveActive, setIsLiveActive] = useState(false);
  const [liveResult, setLiveResult] = useState(null);
  const [liveStatus, setLiveStatus] = useState('IA en espera');
  const [liveError, setLiveError] = useState('');
  const [liveSessionId, setLiveSessionId] = useState(null);
  const [liveSessionStats, setLiveSessionStats] = useState(null);
  const [liveSessionSummary, setLiveSessionSummary] = useState(null);

  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const recorderRef = useRef(null);
  const overlayRef = useRef(null);
  const captureCanvasRef = useRef(null);
  const liveIntervalRef = useRef(null);
  const liveRequestRef = useRef(false);
  const webcamChannelRef = useRef(webcamChannel);
  const liveSessionIdRef = useRef(liveSessionId);

  const emotionOptions = availableEmotions.length > 0 ? availableEmotions : metadata?.labels || [];

  const refreshHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError('');
    try {
      const response = await fetchMediaHistory({
        limit: 12,
        mediaType: historyFilters.mediaType,
        emotion: historyFilters.emotion,
      });
      setHistory(response.items || []);
      setAvailableEmotions(response.filters?.available_emotions || []);
    } catch (error) {
      setHistoryError(error.response?.data?.message || 'No se pudo cargar el historial.');
    } finally {
      setHistoryLoading(false);
    }
  }, [historyFilters]);

  const pushAnalyses = useCallback(
    (analyses = []) => {
      if (!Array.isArray(analyses) || analyses.length === 0) {
        return;
      }
      setLatestResults((prev) => [...analyses, ...prev].slice(0, 5));
      const filtered = analyses.filter((analysis) => {
        const matchesType =
          historyFilters.mediaType === 'all' || analysis.media_type === historyFilters.mediaType;
        const matchesEmotion =
          historyFilters.emotion === 'all' || analysis.dominant_emotion === historyFilters.emotion;
        return matchesType && matchesEmotion;
      });
      if (filtered.length > 0) {
        setHistory((prev) => [...filtered, ...prev].slice(0, 12));
      }
      refreshHistory().catch(() => {});
    },
    [historyFilters, refreshHistory]
  );

  const closeLiveSession = useCallback(async () => {
    const sessionId = liveSessionIdRef.current;
    if (!sessionId) {
      return null;
    }
    try {
      const response = await stopLiveSession(sessionId);
      setLiveSessionSummary(response);
      setLiveSessionStats(response);
      if (response.analyses?.length) {
        pushAnalyses(response.analyses);
      }
      return response;
    } catch (error) {
      setLiveError(error.response?.data?.message || 'No se pudo cerrar la sesión en vivo.');
      return null;
    } finally {
      setLiveSessionId(null);
      liveSessionIdRef.current = null;
    }
  }, [pushAnalyses]);

  const clearOverlay = useCallback(() => {
    const canvas = overlayRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }, []);

  const stopLiveLoop = useCallback(async () => {
    if (liveIntervalRef.current) {
      clearInterval(liveIntervalRef.current);
      liveIntervalRef.current = null;
    }
    liveRequestRef.current = false;
    const hadSession = Boolean(liveSessionIdRef.current);
    setIsLiveActive(false);
    setLiveStatus('IA en espera');
    setLiveResult(null);
    if (!hadSession) {
      setLiveSessionStats(null);
    }
    clearOverlay();
    if (hadSession) {
      await closeLiveSession();
    }
  }, [clearOverlay, closeLiveSession]);

  const drawDetections = useCallback((summary) => {
    const overlay = overlayRef.current;
    const videoElement = videoRef.current;
    if (!overlay || !videoElement) {
      return;
    }
    const displayWidth = videoElement.clientWidth || videoElement.videoWidth;
    const displayHeight = videoElement.clientHeight || videoElement.videoHeight;
    const intrinsicWidth = videoElement.videoWidth || displayWidth;
    const intrinsicHeight = videoElement.videoHeight || displayHeight;
    if (!displayWidth || !displayHeight || !intrinsicWidth || !intrinsicHeight) {
      return;
    }

    overlay.width = displayWidth;
    overlay.height = displayHeight;
    overlay.style.width = `${displayWidth}px`;
    overlay.style.height = `${displayHeight}px`;
    const ctx = overlay.getContext('2d');
    ctx.clearRect(0, 0, overlay.width, overlay.height);

    const scaleX = displayWidth / intrinsicWidth;
    const scaleY = displayHeight / intrinsicHeight;

    const detections = summary?.detections || [];
    if (detections.length === 0) {
      setLiveStatus('IA en vivo: buscando rostros...');
      return;
    }

    ctx.lineWidth = 2;
    ctx.font = `${Math.max(14, overlay.width * 0.018)}px 'Space Grotesk', sans-serif`;
    detections.forEach(({ box, label, confidence }) => {
      const [rawX, rawY, rawW, rawH] = box;
      const x = rawX * scaleX;
      const y = rawY * scaleY;
      const w = rawW * scaleX;
      const h = rawH * scaleY;
      ctx.strokeStyle = '#22d3ee';
      ctx.strokeRect(x, y, w, h);

      const text = `${label} ${(confidence * 100).toFixed(1)}%`;
      const textWidth = ctx.measureText(text).width + 10;
      const textHeight = parseInt(ctx.font, 10) + 6;
      const labelY = Math.max(y - textHeight, 0);

      ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
      ctx.fillRect(x - 2, labelY, textWidth, textHeight);
      ctx.fillStyle = '#fff';
      ctx.fillText(text, x + 2, labelY + 4);
    });
  }, [setLiveStatus]);

  useEffect(() => {
    if (typeof document !== 'undefined' && !captureCanvasRef.current) {
      captureCanvasRef.current = document.createElement('canvas');
    }
    return () => {
      captureCanvasRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    webcamChannelRef.current = webcamChannel;
  }, [webcamChannel]);

  useEffect(() => {
    liveSessionIdRef.current = liveSessionId;
  }, [liveSessionId]);

  useEffect(() => {
    refreshHistory().catch(() => {});
  }, [refreshHistory]);

  useEffect(() => {
    const loadBootstrapData = async () => {
      try {
        const metaResponse = await fetchModelMetadata();
        setMetadata(metaResponse);
      } catch (error) {
        setWebcamError(error.response?.data?.message || 'No se pudo obtener la configuración del modelo.');
      }
    };
    loadBootstrapData();
    return () => {
      stopCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateHistoryFilter = (field) => (event) => {
    const value = event.target.value;
    setHistoryFilters((prev) => ({ ...prev, [field]: value }));
  };

  const handleImageSubmit = async (event) => {
    event.preventDefault();
    if (!imageFile) {
      setImageError('Selecciona una imagen antes de enviar.');
      return;
    }
    setImageLoading(true);
    setImageError('');
    try {
      const response = await analyzeImageUpload(imageFile, imageChannel);
      pushAnalyses(response.analyses);
    } catch (error) {
      setImageError(error.response?.data?.message || 'No se pudo analizar la imagen.');
    } finally {
      setImageLoading(false);
    }
  };

  const handleVideoSubmit = async (event) => {
    event.preventDefault();
    if (!videoFile) {
      setVideoError('Selecciona un video MP4/WebM antes de enviar.');
      return;
    }
    setVideoLoading(true);
    setVideoError('');
    try {
      const response = await analyzeVideoUpload(videoFile, videoChannel);
      pushAnalyses(response.analyses);
    } catch (error) {
      setVideoError(error.response?.data?.message || 'No se pudo analizar el video.');
    } finally {
      setVideoLoading(false);
    }
  };

  const startCamera = async () => {
    if (isPreviewActive) return;
    if (!navigator.mediaDevices?.getUserMedia) {
      setWebcamError('La API de cámara no está disponible en este navegador.');
      setLiveError('');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsPreviewActive(true);
      setWebcamError('');
      setLiveError('');
      setLiveStatus('IA en espera');
      setLiveResult(null);
      setLiveSessionStats(null);
      setLiveSessionSummary(null);
      clearOverlay();
    } catch (error) {
      setWebcamError('No pudimos acceder a la cámara. Revisa los permisos del navegador o cierra otras aplicaciones que la estén usando.');
      setLiveError('');
    }
  };

  const stopCamera = useCallback(() => {
    stopLiveLoop().catch(() => {});
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsPreviewActive(false);
    setIsRecording(false);
    setRecordingBlob(null);
    setLiveError('');
    setLiveResult(null);
    setLiveStatus('IA en espera');
  }, [stopLiveLoop]);

  const startLiveLoop = useCallback(async () => {
    if (!streamRef.current || !videoRef.current) {
      setLiveError('Activa la cámara antes de iniciar la IA en vivo.');
      return;
    }
    if (!captureCanvasRef.current && typeof document !== 'undefined') {
      captureCanvasRef.current = document.createElement('canvas');
    }
    if (liveIntervalRef.current || liveRequestRef.current || liveSessionIdRef.current) {
      return;
    }

    let sessionResponse;
    try {
      sessionResponse = await startLiveSession(webcamChannelRef.current);
    } catch (error) {
      const apiMessage = error.response?.data?.message || error.response?.data?.msg;
      if (error.response?.status === 401 || error.response?.status === 422) {
        setLiveError('Tu sesión expiró. Inicia sesión nuevamente para usar la cámara en vivo.');
      } else {
        setLiveError(apiMessage || 'No se pudo iniciar la sesión en vivo.');
      }
      return;
    }
    setLiveSessionId(sessionResponse.session_id);
    liveSessionIdRef.current = sessionResponse.session_id;
    setLiveSessionStats(null);
    setLiveSessionSummary(null);

    const captureAndAnalyze = async () => {
      if (!videoRef.current?.videoWidth || !captureCanvasRef.current) {
        return;
      }
      if (liveRequestRef.current) {
        return;
      }
      liveRequestRef.current = true;

      const canvas = captureCanvasRef.current;
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.9));
      if (!blob) {
        liveRequestRef.current = false;
        return;
      }

      try {
        const file = new File([blob], `webcam-frame-${Date.now()}.jpg`, { type: 'image/jpeg' });
        const response = await analyzeWebcamFrame(
          file,
          webcamChannelRef.current,
          liveSessionIdRef.current,
        );
        setLiveResult(response);
        setLiveStatus(`IA en vivo: ${response.dominant_emotion} ${(response.confidence * 100).toFixed(1)}%`);
        drawDetections(response);
        setLiveError('');
        if (response.session) {
          setLiveSessionStats(response.session);
        }
      } catch (error) {
        const apiMessage = error.response?.data?.message || 'No se pudo analizar el fotograma de la cámara.';
        if (error.response?.status === 400) {
          setLiveStatus(`IA en vivo: ${apiMessage}`);
          setLiveError('');
          clearOverlay();
        } else {
          setLiveError(apiMessage);
          stopLiveLoop().catch(() => {});
        }
      } finally {
        liveRequestRef.current = false;
      }
    };

    setIsLiveActive(true);
    setLiveStatus('IA en vivo: calibrando cámara...');
    setLiveError('');
    captureAndAnalyze();
    liveIntervalRef.current = window.setInterval(captureAndAnalyze, 1800);
  }, [drawDetections, stopLiveLoop]);

  useEffect(() => {
    if (!isPreviewActive) {
      return undefined;
    }
    const handleKeyPress = (event) => {
      const key = event.key?.toLowerCase();
      if (key === 'p') {
        event.preventDefault();
        startLiveLoop().catch(() => {});
      } else if (key === 'q') {
        event.preventDefault();
        if (isLiveActive) {
          stopLiveLoop().catch(() => {});
        }
        stopCamera();
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [isPreviewActive, isLiveActive, startLiveLoop, stopLiveLoop, stopCamera]);

  const startRecording = () => {
    if (!streamRef.current) {
      setWebcamError('Activa la cámara antes de grabar.');
      return;
    }
    if (isRecording) return;
    if (typeof MediaRecorder === 'undefined') {
      setWebcamError('MediaRecorder no es compatible con este navegador.');
      return;
    }

    let recorder;
    try {
      recorder = new MediaRecorder(streamRef.current, {
        mimeType: 'video/webm;codecs=vp9',
      });
    } catch (error) {
      try {
        recorder = new MediaRecorder(streamRef.current);
      } catch (err) {
        setWebcamError('No se pudo iniciar la grabación en este navegador.');
        return;
      }
    }
    const chunks = [];
    recorder.ondataavailable = (event) => {
      if (event.data?.size) {
        chunks.push(event.data);
      }
    };
    recorder.onstop = () => {
      setIsRecording(false);
      const blob = new Blob(chunks, { type: 'video/webm' });
      setRecordingBlob(blob);
    };
    recorder.onerror = () => {
      setWebcamError('Ocurrió un error durante la grabación.');
      recorder.stop();
    };

    recorder.start();
    recorderRef.current = recorder;
    setIsRecording(true);

    setTimeout(() => {
      if (recorder.state !== 'inactive') {
        recorder.stop();
      }
    }, 5000);
  };

  const stopRecording = () => {
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop();
    }
  };

  const handleWebcamSubmit = async () => {
    if (!recordingBlob) {
      setWebcamError('Graba un clip antes de enviarlo.');
      return;
    }
    setWebcamLoading(true);
    setWebcamError('');
    try {
      const file = new File([recordingBlob], `webcam-${Date.now()}.webm`, { type: recordingBlob.type || 'video/webm' });
      const response = await analyzeWebcamUpload(file, webcamChannel);
      pushAnalyses(response.analyses);
      setRecordingBlob(null);
    } catch (error) {
      setWebcamError(error.response?.data?.message || 'No se pudo analizar la captura de la cámara.');
    } finally {
      setWebcamLoading(false);
    }
  };

  const livePanelData = liveSessionStats || liveResult;
  const livePanelCounts = livePanelData?.counts || {};
  const liveSummaryAnalyses = liveSessionSummary?.analyses?.length
    ? liveSessionSummary.analyses
    : liveSessionSummary?.analysis
    ? [liveSessionSummary.analysis]
    : [];
  const liveSummaryPrimary = liveSummaryAnalyses[0];
  const resolveEmotionCount = (analysis) => {
    if (!analysis) return 0;
    if (analysis.detections?.emotion_count != null) {
      return analysis.detections.emotion_count;
    }
    if (analysis.detections?.counts?.[analysis.dominant_emotion] != null) {
      return analysis.detections.counts[analysis.dominant_emotion];
    }
    if (analysis.emotion_counts?.length) {
      return analysis.emotion_counts[0].count;
    }
    return 1;
  };

  return (
    <section className="app-container">
      {/* Filtro de emociones removido por solicitud */}
      <div className="page-header">
        <h1 className="page-title">Laboratorio multimedia</h1>
        <p className="page-subtitle">
          Carga imágenes, videos o captura directamente desde la cámara para detectar emociones en tiempo real.
        </p>
      </div>

      {metadata && (
        <div className="card media-info-card">
          <h3>Modelo activo</h3>
          <p>Pesos: {metadata.weights_path}</p>
          <div className="media-pills">
            {metadata.labels?.map((label) => (
              <span className="media-pill" key={label}>
                {label}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="media-camera-wrapper">
        <div className="card media-card media-webcam-card">
          <h3>Capturar desde la cámara</h3>
          <p>Activa la cámara, habilita la IA en vivo para ver detecciones sobre el rostro o graba un clip de 5 segundos.</p>
          <div className="media-webcam">
            <div className="media-webcam-layout">
              <div className="media-webcam-preview">
                <video ref={videoRef} className="media-preview" autoPlay muted playsInline />
                <canvas ref={overlayRef} className="media-overlay" />
              </div>
              <div className="media-webcam-panel">
                <div className="media-live-status">
                  <span className={`media-live-indicator ${isLiveActive ? 'on' : ''}`} />
                  <div>
                    <p className="media-live-headline">{liveStatus}</p>
                    {livePanelData && (
                      <p className="media-live-subtitle">
                        Dominante: <strong>{livePanelData.dominant_emotion || 'Sin detección'}</strong> · {((livePanelData.confidence ?? 0) * 100).toFixed(1)}%
                      </p>
                    )}
                  </div>
                </div>
                <div className="media-actions">
                  <button type="button" className="secondary-btn" onClick={startCamera} disabled={isPreviewActive}>
                    Activar cámara
                  </button>
                  <button type="button" className="secondary-btn" onClick={stopCamera}>
                    Detener cámara
                  </button>
                  <button type="button" className="secondary-btn" onClick={startRecording} disabled={!isPreviewActive || isRecording}>
                    {isRecording ? 'Grabando...' : 'Grabar 5s'}
                  </button>
                  <button type="button" className="secondary-btn" onClick={stopRecording} disabled={!isRecording}>
                    Detener grabación
                  </button>
                </div>
                <div className="media-actions media-live-actions">
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => startLiveLoop().catch(() => {})}
                    disabled={!isPreviewActive || isLiveActive}
                  >
                    {isLiveActive ? 'IA en vivo activa' : 'Activar IA en vivo'}
                  </button>
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => stopLiveLoop().catch(() => {})}
                    disabled={!isLiveActive && !liveSessionId}
                  >
                    Detener IA en vivo
                  </button>
                </div>
                <p className="media-hint">
                  Atajos: presiona <strong>P</strong> para iniciar la IA en vivo y <strong>Q</strong> para detener la cámara.
                </p>
                {recordingBlob && <p className="media-hint">Clip listo para enviar ({(recordingBlob.size / 1024 / 1024).toFixed(2)} MB)</p>}
                {/* Label de canal eliminado */}
                {webcamError && <p className="media-error">{webcamError}</p>}
                {liveError && <p className="media-error">{liveError}</p>}
                <button className="primary-btn" type="button" onClick={handleWebcamSubmit} disabled={webcamLoading || !recordingBlob}>
                  {webcamLoading ? 'Enviando...' : 'Analizar clip grabado'}
                </button>
                {livePanelData && (
                  <div className="media-live-panel">
                    <p className="media-live-emotion">
                      {livePanelData.dominant_emotion || 'Sin detección'}
                      <span>{((livePanelData.confidence ?? 0) * 100).toFixed(1)}%</span>
                    </p>
                    {Object.keys(livePanelCounts).length > 0 && (
                      <div className="media-live-counts">
                        {Object.entries(livePanelCounts).map(([label, qty]) => (
                          <span key={label}>
                            {label}
                            <strong>{qty}</strong>
                          </span>
                        ))}
                      </div>
                    )}
                    {liveSessionStats?.frames && (
                      <p className="media-hint" style={{ margin: 0 }}>
                        Muestras procesadas: {liveSessionStats.frames}
                        {liveSessionSummary?.duration_seconds && (
                          <span> · Duración {(liveSessionSummary.duration_seconds / 60).toFixed(1)} min</span>
                        )}
                      </p>
                    )}
                  </div>
                )}
                {liveSummaryAnalyses.length > 0 && liveSummaryPrimary && (
                  <div className="media-live-panel" style={{ background: 'rgba(22, 163, 74, 0.1)' }}>
                    <p className="media-live-emotion" style={{ fontSize: '1rem' }}>
                      Sesión guardada correctamente
                      <span>
                        {new Date(liveSummaryPrimary.created_at).toLocaleTimeString()} · {liveSummaryAnalyses.length}{' '}
                        {liveSummaryAnalyses.length === 1 ? 'emoción' : 'emociones'}
                      </span>
                    </p>
                    <div className="media-links">
                      {liveSummaryPrimary.snapshot_url && (
                        <a href={liveSummaryPrimary.snapshot_url} target="_blank" rel="noreferrer">
                          Ver captura principal
                        </a>
                      )}
                      {liveSummaryPrimary.original_url && (
                        <a href={liveSummaryPrimary.original_url} target="_blank" rel="noreferrer">
                          Descargar sesión
                        </a>
                      )}
                    </div>
                    <div className="media-live-counts">
                      {liveSummaryAnalyses.map((analysis) => (
                        <span key={`live-summary-${analysis.id}`}>
                          {analysis.dominant_emotion}
                          <strong>{resolveEmotionCount(analysis)}</strong>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="media-upload-grid">
        <div className="card media-card">
          <h3>Analizar imagen</h3>
          <p>Carga una fotografía (JPG, PNG, WEBP) y obtén el sentimiento dominante.</p>
          <form onSubmit={handleImageSubmit} className="media-form">
            <input type="file" accept="image/*" onChange={(event) => setImageFile(event.target.files?.[0] || null)} />
            {/* Selector de canal eliminado completamente */}
            {imageError && <p className="media-error">{imageError}</p>}
            <button className="primary-btn" type="submit" disabled={imageLoading}>
              {imageLoading ? 'Analizando...' : 'Procesar imagen'}
            </button>
          </form>
        </div>

        <div className="card media-card">
          <h3>Analizar video</h3>
          <p>Sube un clip MP4/MOV/WebM para procesar múltiples fotogramas.</p>
          <form onSubmit={handleVideoSubmit} className="media-form">
            <input type="file" accept="video/mp4,video/webm,video/quicktime" onChange={(event) => setVideoFile(event.target.files?.[0] || null)} />
            {/* Selector de canal eliminado completamente */}
            {videoError && <p className="media-error">{videoError}</p>}
            <button className="primary-btn" type="submit" disabled={videoLoading}>
              {videoLoading ? 'Analizando...' : 'Procesar video'}
            </button>
          </form>
        </div>
      </div>

      {latestResults.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Últimos resultados</h2>
          <div className="media-result-list">
            {latestResults.map((item) => (
              <MediaResultCard key={`${item.id}-${item.created_at}`} item={item} />
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: '2rem' }}>
        <div className="media-history-header">
          <h2>Historial almacenado</h2>
          <div className="media-filter-bar">
            <label>
              Tipo de medio
              <select value={historyFilters.mediaType} onChange={updateHistoryFilter('mediaType')}>
                <option value="image">Fotos</option>
                <option value="video">Videos</option>
                <option value="all">Todos</option>
              </select>
            </label>
            <label>
              Sentimiento
              <select value={historyFilters.emotion} onChange={updateHistoryFilter('emotion')}>
                <option value="all">Todos</option>
                {emotionOptions.map((label) => (
                  <option key={label} value={label}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
        {historyError && <p className="media-error">{historyError}</p>}
        {historyLoading ? (
          <p className="media-hint">Cargando registros...</p>
        ) : history.length === 0 ? (
          <p className="media-hint">Aún no hay registros almacenados para este usuario.</p>
        ) : (
          <div className="media-result-list">
            {history.map((item) => (
              <MediaResultCard key={`history-${item.id}`} item={item} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

export default MediaLab;
