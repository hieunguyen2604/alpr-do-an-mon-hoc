# Bản đồ trích dẫn — BibTeX ↔ báo cáo Phase 1

*Cập nhật: 19/07/2026*

## Mục đích

Sáu báo cáo trong `docs/reports/` dẫn nguồn bằng **URL markdown nội tuyến** để đọc trực tiếp được trên GitHub, 
còn `docs/references.bib` dùng **khóa BibTeX**. Tài liệu này là bảng ánh xạ giữa hai dạng đó, để khi viết quyển 
luận văn ở **Phase 9** không phải dò tay hàng trăm trích dẫn.

**Cách dùng:** tìm nguồn trong báo cáo → tra dòng tương ứng ở đây → lấy khóa BibTeX → viết `\cite{khóa}`.

> **Không đổi 6 báo cáo sang cú pháp `\cite{}`.** Làm vậy sẽ phá khả năng đọc trực tiếp trên GitHub — 
> đó chính là lý do các báo cáo dùng URL nội tuyến ngay từ đầu. Bảng này tồn tại để giữ **cả hai** dạng.

## Quy ước cột

| Cột | Nội dung |
|---|---|
| **Khóa BibTeX** | Khóa tra trong `docs/references.bib` |
| **Nguồn** | Nhan đề rút gọn của entry |
| **Trích ở đâu** | Tên rút gọn của báo cáo + **số mục** chứa trích dẫn |

Tên rút gọn báo cáo: `research` = `01-research-report.md`, `yolo` = `01-yolo-comparison.md`, 
`ocr` = `01-ocr-comparison.md`, `dataset` = `01-dataset-survey.md`, `vn-plate` = `01-vn-plate-standards.md`, 
`tech` = `01-technology-comparison.md`.

Số mục lấy từ tiêu đề gần nhất phía trên vị trí trích dẫn; khi tiêu đề không đánh số thì ghi tên tiêu đề. 
Một entry được trích ở nhiều chỗ chỉ liệt kê **tối đa 4 mục đầu**, phần còn lại ký hiệu `…`.

**Tổng: 232 entry** — 211 đã được trích dẫn, 21 thuộc nhóm *Further reading (not cited)*.

---

## ALPR Literature

| Khóa BibTeX | Nguồn | Trích ở đâu (báo cáo — mục) |
|---|---|---|
| `anagnostopoulos_2008_survey` | License Plate Recognition From Still Images and Video Sequences: A Survey | **research**: 2.2.3, A. Khảo sát và tổng quan |
| `springer_2012_edgemorphology` | License Plate Localization Based on Edge Detection and Morphology | **research**: 2.3.1, B. Phương pháp cổ điển |
| `ieee_2013_edgegeometrical` | License plate localization based on edge-geometrical features using morphological approach | **research**: 2.3.1, B. Phương pháp cổ điển |
| `du_2013_review` | Automatic License Plate Recognition (ALPR): A State-of-the-Art Review | **research**: 2.2.3 |
| `hsu_2013_aolp` | Application-Oriented License Plate Recognition | **research**: 2.2.2, E. Bộ dữ liệu và benchmark |
| `zherzdev_2018_lprnet` | LPRNet: License Plate Recognition via Deep Neural Networks | **ocr**: 7.1; **research**: 2.4.2, 2.5.1, C. Deep learning — kiến trúc và phươ… |
| `laroca_2018_yolo` | A Robust Real-Time Automatic License Plate Recognition Based on the YOLO Detector | **research**: 2.3.2, 2.4.2, 2.5.1, C. Deep learning — kiến trúc và phươ… |
| `silva_2018_wpodnet` | License Plate Detection and Recognition in Unconstrained Scenarios | **research**: 2.2.3, 2.3.2, C. Deep learning — kiến trúc và phươ… |
| `xu_2018_ccpd` | Towards End-to-End License Plate Detection and Recognition: A Large Dataset and Baseline | **dataset**: 3, 3.1, 9.1; **research**: 2.6.2 |
| `li_2019_endtoend` | Toward End-to-End Car License Plate Detection and Recognition With Deep Neural Networks | **research**: 2.3.3, 2.4.1, 2.5.1, C. Deep learning — kiến trúc và phươ… |
| `zhang_2020_attentional` | A Robust Attentional Framework for License Plate Recognition in the Wild | **research**: 2.4.2, 2.5.1, 2.6.1, C. Deep learning — kiến trúc và phươ… |
| `laroca_2021_layout` | An efficient and layout-independent automatic license plate recognition system based on the YOLO detector | **research**: 2.2.3, 2.4.3, 2.5.1, C. Deep learning — kiến trúc và phươ… |
| `wang_2021_vsnet` | Rethinking and Designing a High-performing Automatic License Plate Recognition Approach | **research**: 2.4.2, 2.5.1, 2.10.1, C. Deep learning — kiến trúc và phươ… |
| `laroca_2022_crossdataset` | On the Cross-Dataset Generalization in License Plate Recognition | **dataset**: 1.1, 3, 4.2.1, 4.2.3 …; **ocr**: 4.1.1, 6.3, 7.1; **research**: 2.5.1, 2.6.3, 2.8.2, 2.8.5 … |
| `batra_2022_yolov5` | A Novel Memory and Time-Efficient ALPR System Based on YOLOv5 | **research**: 2.5.1, 2.9.1, 2.10.2, C. Deep learning — kiến trúc và phươ… |
| `velarde_2022_benchmarking` | Benchmarking Algorithms for Automatic License Plate Recognition | **research**: 2.5.1, E. Bộ dữ liệu và benchmark |
| `ieee_2022_easyocrtesseract` | Comparative Analysis of EasyOCR and TesseractOCR for Automatic License Plate Recognition using Deep Learning Algorithm | **ocr**: 3.1, 6.6, 7.2 |
| `reddy_2024_yolov8ocr` | License Plate Detection using YOLO v8 and Performance Evaluation of EasyOCR, PaddleOCR and Tesseract | **ocr**: 3.3, 6.6, 7.2 |
| `tao_2024_pdlpr` | A Real-Time License Plate Detection and Recognition Model in Unconstrained Scenarios | **research**: C. Deep learning — kiến trúc và phươ… |
| `nascimento_2024_lpsr` | Enhancing License Plate Super-Resolution: A Layout-Aware and Character-Driven Approach | **research**: 2.5.1, 2.10.2, D. Vision-Language Model và hướng si… |
| `aldahoul_2024_vehiclepaligemma` | Advancing Vehicle Plate Recognition: Multitasking Visual Language Models with VehiclePaliGemma | **research**: 2.3.3, 2.5.1, 2.5.2, 2.10.1 … |
| `shpir_2025_diffusion` | License Plate Images Generation with Diffusion Models | **research**: 2.5.1, 2.10.1, 2.10.2, D. Vision-Language Model và hướng si… |
| `meyer_2025_salt` | Relaxed syntax modeling in Transformers for future-proof license plate recognition | **research**: 2.2.1, 2.5.1, 2.8.4, 2.10.1 … |
| `xu_2025_lptraflnet` | LPTR-AFLNet: Lightweight Integrated Chinese License Plate Rectification and Recognition Network | **ocr**: 1.2, 2.9, 4.3.1, 4.3.3 …; **research**: 2.5.1, 2.10.2, C. Deep learning — kiến trúc và phươ… |
| `arxiv_2025_translprnet` | TransLPRNet: Lite Vision-Language Network for Single/Dual-line Chinese License Plate Recognition | **dataset**: 4.2.1, 8.3, 9.1; **ocr**: 2.9, 4.3.4, 6.4, 7.1; **research**: 2.6.3, C. Deep learning — kiến trúc và phươ… |
| `arxiv_2025_patrolvision` | PatrolVision: Automated License Plate Recognition in the wild | **ocr**: 4.1.1, 4.3.5, 7.1 |
| `shabaninia_2025_layoutindependent` | Layout-Independent License Plate Recognition via Integrated Vision and Language Models | **research**: 2.3.3, 2.4.2, 2.4.3, 2.5.1 … |
| `vargoorani_2025_pseudolabel` | Efficient License Plate Recognition via Pseudo-Labeled Supervision with Grounding DINO and YOLOv8 | **research**: 2.5.1, 2.9.4, 2.10.2, D. Vision-Language Model và hướng si… |
| `nascimento_2025_lpsrbenchmark` | Toward Advancing License Plate Super-Resolution in Real-World Scenarios: A Dataset and Benchmark | **research**: 2.10.2, D. Vision-Language Model và hướng si… |
| `gong_2026_lpllm` | LP-LLM: End-to-End Real-World Degraded License Plate Text Recognition via Large Multimodal Models | **research**: 2.3.3, 2.4.2, 2.5.1, 2.10.2 … |
| `laroca_2026_icprlrlpr` | ICPR 2026 Competition on Low-Resolution License Plate Recognition | **research**: 2.5.1, 2.6.1, 2.9.3, 2.10.1 … |
| `li_2026_review` | A detailed review on license plate detection and recognition methods | **research**: 2.2.3, A. Khảo sát và tổng quan |
| `sciencedirect_2026_omanplates` | Comparative study of YOLO models for Oman car plate detection | **yolo**: 8.2, 10.4 |
| `scirep_2025_advanceddl` | Advanced deep learning techniques for automated license plate recognition | **yolo**: 1.2, 8.4, 10.4 |
| `scirep_2024_yolov8ocr` | Enhancing automated vehicle identification by integrating YOLO v8 and OCR techniques for high-precision license plate detection and recognition | **ocr**: 5.1, 7.1, A.1. Số liệu BỊ BÁC BỎ (REFUTED) — t… |
| `jaic_2025_yolov11alpr` | Automatic License Plate Detection System with YOLOv11 Algorithm | **yolo**: 8.3, 10.4 |
| `sutikno_2025_clahe` | Enhanced Automatic License Plate Detection and Recognition using CLAHE and YOLOv11 for Seat Belt Compliance Detection | **yolo**: 8.3, 10.4 |
| `etasr_2025_optimizedyolov8` | Optimized YOLOv8 for Automatic License Plate Recognition on Resource Constrained Devices | **yolo**: 8.3, 10.4 |
| `jcosine_2025_yolo11plate` | Vehicle License Plate Number Detection with YOLO11 | **yolo**: 8.3, 10.4 |
| `arxiv_2024_ocrpreprocessing` | Comparison of Image Preprocessing Techniques for Vehicle License Plate Recognition Using OCR | **ocr**: 7.1 |
| `arxiv_2026_multinationalfusion` | Advancing Multinational License Plate Recognition Through Synthetic and Real Data Fusion: A Comprehensive Evaluation | **ocr**: 6.4, 7.1 |
| `arxiv_2026_embeddedlpr` | An Embedded Real-Time License Plate Recognition System for Complex Traffic Scenes | **ocr**: 4.3.5, 7.1 |
| `ultralytics_2025_anprblog` | Using Ultralytics YOLO11 for Automatic Number Plate Recognition | **yolo**: 10.4 |
| `acm_2012_tollbooth` | Building a license plate recognition system for Vietnam tollbooth | **research**: 2.7.1, F. Công trình và dữ liệu về biển số … |
| `amr_2012_charsegmentation` | Research on Characters Segmentation in One-Row and Two-Row of Vietnam License Plates | **ocr**: 7.1, PA-3 — Horizontal projection (peak-t… |
| `jics_nd_edgeneural` | Vietnam License Plate Recognition System based on Edge Detection and Neural Networks | **research**: F. Công trình và dữ liệu về biển số … |
| `lqdtu_2021_vietnameselpr` | An efficient method to improve the accuracy of Vietnamese vehicle license plate recognition in unconstrained environment | **ocr**: 6.6, 7.2; **research**: 2.7.1, 2.7.2, 2.9.1, F. Công trình và dữ liệu về biển số … |
| `trananh_2023_multiangle` | License Plate Recognition Based on Multi-Angle View Model | **dataset**: 2.2, 9.1; **ocr**: 4.3.6, 7.1; **research**: 2.7.1, F. Công trình và dữ liệu về biển số … |
| `le_2023_vnmotorcycle` | Robust Vietnam's Motorcycle License Plate Detection and Recognition Using Deep Learning Model | **ocr**: 4.3.5, 6.4, 7.1; **research**: 2.2.3, 2.7.1, F. Công trình và dữ liệu về biển số … |
| `tran_2023_openalpr` | Building Vietnam's License Plate Recognition System Based on OpenALPR | **dataset**: 5.5, 9.1; **research**: 2.7.1, F. Công trình và dữ liệu về biển số … |
| `nguyen_2023_yolov5bienso` | Đề xuất mô hình YOLO V5 ứng dụng trong nhận diện biển số xe | **research**: 2.7.1, F. Công trình và dữ liệu về biển số … |
| `dang_2024_crnn` | Vietnam Vehicle Number Recognition Based on an Improved CRNN with Attention Mechanism | **research**: 2.7.1, 2.9.2, F. Công trình và dữ liệu về biển số … |
| `dlu_2024_yolov8nas` | Nghiên cứu các phiên bản YOLOv8 và YOLO-NAS trong phát hiện biển số xe | **research**: 2.7.1, F. Công trình và dữ liệu về biển số … |
| `tran_2024_embeddedlpr` | Implementation of a License Plate Recognition System in Vietnam Using Embedding Devices | **ocr**: 7.1; **research**: 2.7.1 |

## YOLO

| Khóa BibTeX | Nguồn | Trích ở đâu (báo cáo — mục) |
|---|---|---|
| `jocher_2023_yolov8` | Ultralytics YOLOv8 | **yolo**: 2.2, 3.1, 4.2, 4.9 … |
| `jocher_2024_yolo11` | Ultralytics YOLO11 | **yolo**: 2.2, 3.4.3, 4.5, 4.9 … |
| `wang_2024_yolov9` | YOLOv9: Learning What You Want to Learn Using Programmable Gradient Information | **yolo**: 2.2, 3.2, 4.3, 4.9 … |
| `wang_2024_yolov9license` | WongKinYiu/yolov9 --- LICENSE.md (GPL-3.0) | **yolo**: 2.2, 7.1, 10.5 |
| `wang_2024_yolov10paper` | YOLOv10: Real-Time End-to-End Object Detection | **yolo**: 3.3, 4.4, 4.10, 10.1 |
| `wang_2024_yolov10` | THU-MIG/yolov10 --- kho ma nguon chinh thuc | **yolo**: 2.2, 3.3, 4.4, 4.9 … |
| `ultralytics_2024_yolov10docs` | YOLOv10 --- tai lieu Ultralytics | **yolo**: 3.3, 4.10, 10.1 |
| `khanam_2024_yolov11overview` | YOLOv11: An Overview of the Key Architectural Enhancements | **yolo**: 2.2, 3.4, 10.1 |
| `tian_2025_yolo12docs` | YOLO12: Attention-Centric Object Detection | **yolo**: 2.2, 3.5, 4.6, 4.9 … |
| `tian_2025_yolov12` | YOLOv12: Attention-Centric Real-Time Object Detectors | **yolo**: 2.2, 4.10, 10.1 |
| `lei_2025_yolov13` | YOLOv13: Real-Time Object Detection with Hypergraph-Enhanced Adaptive Visual Perception | **yolo**: 2.2, 3.6, 4.6, 4.10 … |
| `imoonlab_2025_yolov13repo` | iMoonLab/yolov13 --- repository chinh thuc (AGPL-3.0) | **yolo**: 2.2, 3.6, 4.6, 4.9 … |
| `jocher_2025_yolo26` | Ultralytics YOLO26 | **yolo**: 2.2, 3.7, 4.10, 9.3 … |
| `ultralytics_2025_yolo11vsyolov8` | YOLO11 vs YOLOv8 --- so sanh chinh thuc | **yolo**: 3.4.3, 4.10, 6.1, 9.1 … |
| `ultralytics_2026_blockpy` | ultralytics/nn/modules/block.py --- dinh nghia C2f, C3k, C3k2, C2PSA, PSABlock, Attention | **yolo**: 3.4, 10.2 |
| `ultralytics_2026_detecttask` | Object Detection task docs --- chu thich phan cung benchmark | **yolo**: 4.1, 10.2, Quy ước trình bày và cảnh báo phương… |
| `arxiv_2025_smallobject` | Small Object Detection with YOLO: A Performance Analysis Across Model Versions and Hardware | **yolo**: 10.5 |

## OCR

| Khóa BibTeX | Nguồn | Trích ở đâu (báo cáo — mục) |
|---|---|---|
| `du_2020_ppocr` | PP-OCR: A Practical Ultra Lightweight OCR System | **ocr**: 2.1, 7.1 |
| `du_2021_ppocrv2` | PP-OCRv2: Bag of Tricks for Ultra Lightweight OCR System | **ocr**: 2.1, 7.1 |
| `paddlepaddle_2025_ocr3report` | PaddleOCR 3.0 Technical Report | **ocr**: 2.1, 7.1 |
| `cui_2026_ppocrv5` | PP-OCRv5: A Specialized 5M-Parameter Model Rivaling Billion-Parameter Vision-Language Models on OCR Tasks | **ocr**: 2.1, 3.1, 5.2, 7.1 |
| `paddlepaddle_2026_ppocrv6` | PP-OCRv6: From 1.5M to 34.5M Parameters, Surpassing Billion-Scale VLMs on OCR Tasks | **ocr**: 2.1, 2.8, 5.2, 7.1 |
| `paddlepaddle_2026_ppocrv5docs` | Introduction to PP-OCRv5 --- PaddleOCR Documentation | **ocr**: 1.2, 3.1, 7.3; **yolo**: 5.8, 10.3 |
| `paddlepaddle_2026_textrecognition` | Text Recognition Module --- PaddleOCR/PaddleX Documentation | **ocr**: 1.2, 2.1, 3.1, 5.2 …; **yolo**: 5.8 |
| `paddlepaddle_2026_textdetection` | Text Detection Module --- PaddleX Documentation | **ocr**: 2.1, 3.1, 5.2, 7.3; **yolo**: 5.8, 10.3 |
| `paddlepaddle_nd_ocrpipeline` | PaddleOCR 3.x --- OCR Pipeline Usage Tutorial | **ocr**: 4.4, 7.3, PA-4 — Phân cụm bounding box theo to… |
| `paddlepaddle_nd_plateapp` | PaddleOCR --- Ung dung nhan dang bien so nhe (CCPD, PP-OCRv3, so lieu fine-tune) | **ocr**: 4.1.4, 5.2, 7.3 |
| `paddlepaddle_nd_sortedboxes` | PaddleOCR tools/infer/predict_system.py --- ham sorted_boxes voi nguong 10 pixel | **ocr**: 7.4, Ba bẫy cụ thể của PaddleOCR — phải x… |
| `paddleocr_2022_discussion7515` | Is there any option to whitelist or blacklist character in PaddleOCR --- Discussion 7515 | **ocr**: 3.1, 5.3, 7.4, Ba bẫy cụ thể của PaddleOCR — phải x… |
| `paddleocr_2024_discussion13457` | Regarding Reading order instructions --- PaddleOCR Discussion 13457 | **ocr**: 7.4 |
| `paddleocr_nd_discussion15011` | PaddleOCR Discussion #15011 --- Word Detection Configuration (det_db_unclip_ratio tuning) | **ocr**: 7.4 |
| `paddleocr_nd_issue14109` | PaddleOCR Issue #14109 --- rec_image_shape mac dinh '3, 48, 320' tu PP-OCRv3 | **ocr**: 7.4 |
| `paddlepaddle_2025_latinrec` | PaddlePaddle/latin_PP-OCRv5_mobile_rec --- Hugging Face | **01-citation-map.md**: ocr; **ocr**: 1.2, 7.4 |
| `paddlepaddle_2026_pypipaddle` | paddlepaddle --- PyPI | **ocr**: 3.1, 5.2, 7.5 |
| `paddlepaddle_2026_pypipaddleocr` | paddleocr --- PyPI | **ocr**: 3.1, 5.2, 6.5, 7.5 |
| `jaided_2026_pypieasyocr` | easyocr --- PyPI | **ocr**: 2.2, 3.1, 6.5, 7.5 |
| `lee_2026_pypipytesseract` | pytesseract --- PyPI | **ocr**: 3.1, 6.5, 7.5 |
| `mindee_2026_pypidoctr` | python-doctr --- PyPI | **ocr**: 3.1, 6.5, 7.5 |
| `felixdittrich_2026_pypionnxtr` | onnxtr --- PyPI | **ocr**: 6.5, 7.5 |
| `openmmlab_2026_pypimmocr` | mmocr --- PyPI | **ocr**: 3.1, 6.5, 7.5 |
| `kandratavicius_2026_pypifastplateocr` | fast-plate-ocr --- PyPI | **ocr**: 3.1, 6.5, 7.5 |
| `rapidai_2026_pypirapidocr` | rapidocr --- PyPI | **ocr**: 2.8, 6.5, 7.5 |
| `rapidai_2026_pypirapidocronnx` | rapidocr-onnxruntime --- PyPI | **01-citation-map.md**: ocr; **ocr**: 2.8, 7.5 |
| `jaided_2025_easyocrdeepwiki` | JaidedAI/EasyOCR --- DeepWiki (kien truc CRAFT + CRNN, kich thuoc model) | **ocr**: 2.2, 3.1, 4.4, 7.4 |
| `jaided_2025_easyocrdocs` | EasyOCR API Documentation | **ocr**: 2.2, 3.1, 7.3 |
| `jaided_2025_easyocrlanguages` | EasyOCR Supported Languages --- DeepWiki | **ocr**: 2.2, 3.1, 4.4, 7.4 |
| `jaided_2026_easyocrrepo` | JaidedAI/EasyOCR --- GitHub | **ocr**: 7.4 |
| `tesseract_2026_releasenotes` | Tesseract Release Notes | **ocr**: 2.3, 3.1, 6.5, 7.3 |
| `rosebrock_2021_psm` | Tesseract Page Segmentation Modes (PSMs) Explained: How to Improve Your OCR Accuracy | **ocr**: 2.3, 3.1, 4.4, 7.7 |
| `rosebrock_2021_whitelist` | Whitelisting and Blacklisting Characters with Tesseract and Python | **ocr**: 2.3, 3.1, 7.7 |
| `li_2021_trocr` | TrOCR: Transformer-based Optical Character Recognition with Pre-trained Models | **ocr**: 2.4, 3.1, 7.1 |
| `roboflow_2025_trocr` | TrOCR --- Roboflow Inference Models | **ocr**: 2.4, 3.1, 4.4, 7.3 |
| `mindee_2026_doctrmodels` | Choosing the right model --- docTR documentation | **ocr**: 2.5, 3.1, 7.3 |
| `mindee_2026_doctrrepo` | mindee/doctr --- GitHub | **ocr**: 7.4 |
| `dittrich_2026_onnxtr` | felixdittrich92/OnnxTR --- GitHub | **ocr**: 2.8, 3.1, 6.1, 7.4 |
| `openmmlab_2023_mmocrrepo` | open-mmlab/mmocr --- GitHub | **ocr**: 2.6, 3.1, 7.4 |
| `openmmlab_2024_mmdeploy` | MMOCR Deployment --- mmdeploy documentation | **ocr**: 2.6, 7.3 |
| `kuang_2021_mmocr` | MMOCR: A Comprehensive Toolbox for Text Detection, Recognition and Understanding | **ocr**: 7.1 |
| `kandratavicius_2026_fastplateocr` | ankandrew/fast-plate-ocr --- GitHub | **ocr**: 2.7, 3.1, 7.4 |
| `fastplateocr_2026_onnxrecognizer` | ONNXPlateRecognizer --- fast-plate-ocr DeepWiki | **ocr**: 2.7, 3.1, 7.4 |
| `kandratavicius_2026_fastalpr` | ankandrew/fast-alpr --- GitHub | **ocr**: 7.4 |
| `rapidai_2026_rapidocr` | RapidAI/RapidOCR --- GitHub | **ocr**: 2.8, 7.4 |
| `tildalice_2025_ocrbenchmark` | PaddleOCR vs EasyOCR vs Tesseract benchmark | **ocr**: 2.2, 2.3, 3.1, 5.3 … |
| `codesota_2026_ocrbenchmark` | PaddleOCR vs Tesseract vs EasyOCR: OCR Speed and Accuracy 2026 | **ocr**: 2.3, 3.1, 5.3, 7.7 |
| `intuitionlabs_2025_nonllmocr` | Technical Analysis of Modern Non-LLM OCR Engines | **ocr**: 7.7 |
| `arxiv_2026_ocrbillbenchmark` | Benchmarking OCR Pipelines with Adaptive Enhancement for Multi-Domain Retail Bill Digitization | **ocr**: 7.1 |
| `arxiv_2019_arbitraryshaped` | A Feasible Framework for Arbitrary-Shaped Scene Text Recognition | **ocr**: 4.1.2, 7.1 |

## Datasets

| Khóa BibTeX | Nguồn | Trích ở đâu (báo cáo — mục) |
|---|---|---|
| `hsu_2013_aolpdataset` | AVLab-AOLP dataset --- trang tai chinh thuc | **research**: E. Bộ dữ liệu và benchmark |
| `hyperai_nd_aolp` | AOLP Application-Oriented License Plate Dataset | **research**: 2.6.1 |
| `openalpr_2016_benchmarks` | OpenALPR benchmarks --- repository chinh thuc | **dataset**: 3, 4.2.4, 9.3; **research**: 2.6.1, E. Bộ dữ liệu và benchmark |
| `xu_2018_ccpdrepo` | CCPD: a diverse and well-annotated dataset for license plate detection and recognition | **dataset**: 3, 3.1, 4.2.1, 9.3 …; **research**: 2.6.1, 2.6.2, E. Bộ dữ liệu và benchmark |
| `binh234_2023_ccpd2019` | ccpd2019 --- Kaggle mirror | **dataset**: 3, 4.2.1, 9.3, Câu hỏi 3: Có nên pre-train trên dữ …; **research**: E. Bộ dữ liệu và benchmark |
| `laroca_2018_ufpralpr` | UFPR-ALPR dataset --- repository chinh thuc | **dataset**: 3, 4.2.2, 6.1, 6.2 …; **research**: 2.2.2, 2.6.1, E. Bộ dữ liệu và benchmark |
| `laroca_nd_ufpralprlicense` | UFPR-ALPR license agreement | **dataset**: 3, 4.2.2, 6.1, 6.2 …; **research**: 2.2.2, 2.6.1, E. Bộ dữ liệu và benchmark |
| `laroca_2022_rodosol` | RodoSol-ALPR dataset --- repository chinh thuc | **dataset**: 3, 9.3; **research**: 2.6.1, E. Bộ dữ liệu và benchmark |
| `wojcik_2025_lplc` | LPLC: A Dataset for License Plate Legibility Classification | **research**: 2.5.1, 2.6.1, 2.10.1, E. Bộ dữ liệu và benchmark |
| `laroca_2026_icprlrlprweb` | ICPR 2026 LRLPR Competition --- trang chinh thuc | **research**: E. Bộ dữ liệu và benchmark, e. bộ dữ liệu và benchmark |
| `agrawal_2024_globallpdataset` | Global License Plate Dataset | **dataset**: 3, 4.2.5, 8.5, 9.1; **research**: 2.6.1, E. Bộ dữ liệu và benchmark |
| `siddagra_nd_globallpdatasetrepo` | Global License Plate Dataset --- repository splits chinh thuc | **dataset**: 3, 4.2.5, 9.3; **research**: E. Bộ dữ liệu và benchmark, e. bộ dữ liệu và benchmark |
| `arxiv_2018_howmanyplates` | How many labeled license plates are needed? | **dataset**: 5.1, 5.4, 7.1, 7.2 …; **research**: 2.7.4, 2.8.5, E. Bộ dữ liệu và benchmark |
| `vapr_2018_mapr` | Vietnamese Bike License Plate Recognition Challenge (MAPR 2018) | **dataset**: 2.2, 9.2; **research**: 2.7.1, F. Công trình và dữ liệu về biển số … |
| `fictlabs_2025_vnlp` | VNLP --- Vietnamese license plate dataset | **dataset**: 2.1, 2.3, 4.1.1, 7.2 …; **research**: 2.7.3, F. Công trình và dữ liệu về biển số … |
| `school_2023_vnlicenseplate` | vietnamese license plate --- Object Detection Dataset | **dataset**: 2.1, 4.1.3, 8.2, 9.2; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `cuongta_2020_vncarplate` | Vietnamese Car License Plate --- Object Detection Dataset | **dataset**: 2.1, 4.1.3, 9.2; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `trafficcamera_nd_vnlicenseplate` | Vietnam License plate --- Object Detection Dataset | **dataset**: 2.1, 9.2; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `licenseplatereg_2025_vnocrplate` | Viet Nam OCR plate --- Object Detection Dataset | **dataset**: 2.1, 4.1.4, 8.2, 9.2; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `vnutvtgl_nd_vnrnp` | VNRNP --- Object Detection Dataset (da bi xoa) | **dataset**: 2.2, 4.1.7, 8.1, 9.2 |
| `datasetformatconversion_nd_vnlpr` | Vietnam-License-Plate-Recognition --- Object Detection Dataset | **01-citation-map.md**: datasets; **dataset**: 2.1, 9.2; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `tran_nd_vnlicenseplate` | Vietnam license-plate --- Object Detection Dataset | **dataset**: 2.1, 9.2; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `nguyen_nd_ericvnlicenseplate` | vietnam license plate --- Object Detection Dataset | **dataset**: 2.1, 9.2; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `nguyen_2023_vnplatesegment` | Vietnam License Plate Segment Datasets | **dataset**: 2.1, 2.3, 4.1.2, 4.1.6 …; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `bomaich_2022_vnlicenseplate` | VNLicensePlate_yolov7 | **dataset**: 2.1, 4.1.6, 9.2; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `topkek69_2024_vnlpocr` | Vietnamese License Plate OCR | **dataset**: 2.1, 4.1.5, 9.2; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `nguyen_2024_chardataset` | Character Dataset For VietNam License Plate | **dataset**: 2.1, 4.1.5, 4.1.6, 9.2; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `huynh_2025_vnlpdetection` | Vietnamese License Plate Detection | **dataset**: 2.1, 4.1.6, 9.2; **research**: 2.7.3, G. Bộ dữ liệu công khai về biển số V… |
| `winter2897_2021_datasetdoc` | Dataset doc --- License Plate Detection & Recognition (VOC/PASCAL + YOLO) | **dataset**: 2.1, 8.1, 9.2; **research**: 2.7.5, H. Mã nguồn mở về biển số Việt Nam |
| `unidatapro_nd_licenseplate` | UniDataPro/license-plate-detection | **01-citation-map.md**: datasets; **dataset**: 2.1, 3, 9.3; **research**: 2.7.3 |
| `roboflow_nd_universedownload` | Download a Universe Dataset --- Roboflow Docs | **dataset**: 9.4; **research**: I. Bối cảnh, giải pháp thương mại và…, i. bối cảnh, giải pháp thương mại và… |
| `roboflow_nd_datasetdownload` | Download a Dataset --- Roboflow Docs (YOLO, COCO JSON, Pascal VOC XML, CreateML, TFRecords, Darknet) | **dataset**: 4.1.3, 8.6, 9.4, Câu hỏi 2: Có nên gộp nhiều bộ không… |

## Legal (Vietnam)

| Khóa BibTeX | Nguồn | Trích ở đâu (báo cáo — mục) |
|---|---|---|
| `bocongan_2024_tt79` | Thông tư số 79/2024/TT-BCA quy định về cấp, thu hồi chứng nhận đăng ký xe, biển số xe cơ giới, xe máy chuyên dùng | **dataset**: 9.5; **research**: I. Bối cảnh, giải pháp thương mại và…, i. bối cảnh, giải pháp thương mại và…; **vn-plate**: 1.1, 1.2, 12.1 |
| `bocongan_2023_tt24` | Thông tư số 24/2023/TT-BCA quy định về cấp, thu hồi đăng ký, biển số xe cơ giới | **dataset**: 9.5; **research**: I. Bối cảnh, giải pháp thương mại và…; **vn-plate**: 12.1 |
| `bocongan_2025_tt13` | Thông tư số 13/2025/TT-BCA sửa đổi, bổ sung một số điều của Thông tư số 79/2024/TT-BCA | **dataset**: 1.2, 9 (mục 36); **ocr**: 4.2; **research**: 2.8.4, 6; **vn-plate**: 1.2, 1.3, 6.1, 12 — *dẫn theo tên văn bản, không kèm URL* |
| `bocongan_2025_tt51` | Thông tư số 51/2025/TT-BCA sửa đổi, bổ sung một số điều của Thông tư số 79/2024/TT-BCA đã được sửa đổi tại Thông tư số 13/2025/TT-BCA | **dataset**: 9.5; **research**: I. Bối cảnh, giải pháp thương mại và…, i. bối cảnh, giải pháp thương mại và…; **vn-plate**: 1.2, 12.1 |
| `boquocphong_2021_tt169` | Thông tư 169/2021/TT-BQP quy định về đăng ký, quản lý, sử dụng xe cơ giới, xe máy chuyên dùng trong Bộ Quốc phòng | **vn-plate**: 12.1 |
| `bocongan_2024_qcvn08` | Quy chuẩn kỹ thuật quốc gia về biển số xe QCVN 08:2024/BCA | **dataset**: 8.5, 9.5; **research**: 2.8.3, I. Bối cảnh, giải pháp thương mại và…; **vn-plate**: 1.2, 6.2, 7.2, 7.6 … |
| `bocongan_2024_nhandienbienso` | Nhận diện màu sắc, seri, ký hiệu biển số xe của cơ quan, tổ chức, cá nhân từ 01/01/2025 | **research**: 2.8.3, I. Bối cảnh, giải pháp thương mại và…; **vn-plate**: 2.1, 5.1, 5.3, 6.1 … |
| `bocongan_2024_cososanxuat` | Từ 01/01/2025, cơ sở sản xuất biển số xe phải được kiểm tra, đánh giá định kỳ 2 năm một lần | **vn-plate**: 7.6, 12.2 |
| `chinhphu_2025_kyhieubienso` | Quy định ký hiệu biển số xe ô tô, xe máy tại các địa phương (theo Thông tư 51/2025/TT-BCA) | **vn-plate**: 2.3, 4.1, 10.5, 12.2 |
| `chinhphu_2023_seribiensoxemay` | Từ 15/8, sêri biển số xe máy cấp cho xe cá nhân có 2 chữ cái | **vn-plate**: 3.1, 3.2, 12.2 |
| `baochinhphu_2024_quychuanbienso` | Quy chuẩn kỹ thuật quốc gia về biển số xe | **ocr**: 7.6, PA-2 — Ngưỡng aspect ratio (khuyến n…, pa-2 — ngưỡng aspect ratio (khuyến n… |
| `conganlangson_2024_tt79` | Một số quy định mới của Thông tư số 79/2024/TT-BCA quy định về cấp, thu hồi chứng nhận đăng ký xe, biển số xe cơ giới, xe máy chuyên dùng | **vn-plate**: 6.3, 12.2 |
| `thuviennhadat_2025_kyhieu34tinh` | Chính thức ký hiệu biển số xe 34 tỉnh thành sau sáp nhập theo Thông tư 51/2025/TT-BCA | **vn-plate**: 2.1, 4.2, 4.3, 4.4 … |
| `thuvienphapluat_2024_sokhonggan` | Các số không gắn trên biển số xe của bất kỳ địa phương nào? | **vn-plate**: 12.3 |
| `thuvienphapluat_2025_mausacseri` | Quy định về màu sắc, seri biển số xe của cơ quan, tổ chức, cá nhân trong nước từ năm 2025 | **vn-plate**: 7.1, 12.3 |
| `thuvienphapluat_2025_bienso1chu1so` | Cảnh báo: biển số xe máy 1 chữ 1 số sẽ chỉ được sử dụng đến ngày 31/12/2025 | **vn-plate**: 3.2, 12.3 |
| `thuvienphapluat_2024_kichthuocbienso` | Quy định về biển số xe từ ngày 01/01/2025 theo Thông tư 79/2024/TT-BCA | **ocr**: 7.6, PA-2 — Ngưỡng aspect ratio (khuyến n…, pa-2 — ngưỡng aspect ratio (khuyến n…; **vn-plate**: 12.3 |
| `thuvienphapluat_2021_biensoquandoi` | Tổng hợp ký hiệu biển số xe quân đội (Thông tư 169/2021/TT-BQP) | **vn-plate**: 10.2, 12.3 |
| `luatvietnam_2025_bangtracuubienso` | Bảng tra cứu biển số xe các tỉnh, thành cả nước mới nhất | **vn-plate**: 12.3 |
| `vnexpress_2025_quydinhbienso` | Quy định về biển số xe từ năm 2025 | **vn-plate**: 2.1, 12.4 |
| `dantri_2025_temotodien` | Từ 2025, ô tô điện được gắn tem nhận diện | **vn-plate**: 12.4 |
| `otocomvn_2025_seridangky` | Bỏ quy định phân biệt seri đăng ký với một số dòng xe | **vn-plate**: 2.2, 12.4 |
| `vietnamnet_2023_biensongoaigiao` | Cách đọc ký hiệu biển số xe ngoại giao, nước ngoài ở Việt Nam | **vn-plate**: 8.4, 10.4, 12.4 |
| `vov_2025_bienso34tinh` | Sau ngày 1/7/2025, biển số xe ở 34 tỉnh, thành sẽ được cấp thế nào? | **vn-plate**: 12.4 |
| `khobiensodep_2025_kyhieudacbiet` | Những quy định bạn cần biết về biển số xe kể từ năm 2025 | **vn-plate**: 5.4, 12.4 |
| `dantri_2024_77trieuxemay` | Việt Nam có 77 triệu xe máy, cứ 1.000 dân có 770 người sở hữu xe máy | **research**: 2.8.1, I. Bối cảnh, giải pháp thương mại và… |
| `wikipedia_2025_biensovietnam` | Biển xe cơ giới Việt Nam | **vn-plate**: 12.4 |
| `wikipedia_nd_vnplatesen` | Vehicle registration plates of Vietnam | **ocr**: 4.3.6, 7.7 |

## Tools & Docs

| Khóa BibTeX | Nguồn | Trích ở đâu (báo cáo — mục) |
|---|---|---|
| `ultralytics_2026_license` | Ultralytics Licensing (AGPL-3.0 va Enterprise) | **yolo**: 7.1, 7.2, 7.3, 9.2 … |
| `ultralytics_2026_modelevaluation` | Model Evaluation Insights --- huong dan vat the nho, imgsz, rect, SAHI tiling | **yolo**: 6.1, 6.2, 10.3 |
| `ultralytics_2026_export` | Model Export with Ultralytics YOLO --- danh sach hon 20 dinh dang xuat va tham so | **yolo**: 1.3, 9.2, 10.3 |
| `ultralytics_2026_benchmark` | Model Benchmarking with Ultralytics YOLO --- che do benchmark tu dong tren CPU | **yolo**: 1.3, 9.2, 9.4, 10.3 |
| `ultralytics_2026_openvinoexport` | Intel OpenVINO Export --- Ultralytics Docs (ma nguon markdown, day du bang benchmark CPU/GPU/NPU) | **yolo**: 5.3, 5.4, 10.2, Quy ước trình bày và cảnh báo phương… |
| `onnxruntime_2025_threading` | Thread management --- ONNX Runtime Performance Tuning (intra/inter op threads, spinning, NUMA) | **tech**: 12.1, (a) Hiệu năng async; **yolo**: 5.5, 10.3 |
| `onnxruntime_2025_quantization` | Quantize ONNX models --- ONNX Runtime (dynamic vs static, VNNI/AVX512, canh bao phan cung cu) | **yolo**: 5.4, 10.3 |
| `openvino_2025_precisioncontrol` | Precision Control --- OpenVINO documentation (FP16 chuyen ve FP32 tren CPU, bf16/AMX) | **tech**: 9.1, 12.1; **yolo**: 5.3, 10.3 |
| `openvino_2024_performancehints` | Performance Hints and Thread Scheduling --- OpenVINO CPU Device (LATENCY hint, hyper-threading, inference_num_threads) | **yolo**: 5.5, 10.3 |
| `nvidia_2026_tensorrtprereq` | TensorRT Prerequisites --- yeu cau bat buoc GPU NVIDIA va CUDA Toolkit | **yolo**: 5.1, 10.3 |
| `learnopencv_2025_yolo11rpi` | YOLO11 on Raspberry Pi: Optimizing Object Detection for Edge | **yolo**: 10.5 |
| `lenovo_2025_xeonopenvino` | Accelerating Real-Time Object Detection: Running YOLO Models on Intel Xeon 6 Processors with OpenVINO | **yolo**: 10.5 |
| `we0091234_nd_chineselpr` | we0091234/Chinese_license_plate_detection_recognition --- YOLOv5, ho tro 12 loai bien Trung Quoc ke ca bien 2 tang | **01-citation-map.md**: tools & docs; **ocr**: 4.3.2, 4.5, 7.4, PA-1 — Dùng chính mạng detection xuấ… … |
| `we0091234_nd_doubleplatesplit` | double_plate_split_merge.py --- code tach va ghep bien 2 tang (5/12 va 1/3 + hstack) | **01-citation-map.md**: tools & docs; **ocr**: 4.3.2, 7.4 |
| `we0091234_nd_detectplate` | detect_plate.py --- phan loai class 0/1 (1 tang / 2 tang), four_point_transform, goi get_split_merge | **ocr**: 4.5, 7.4, PA-1 — Dùng chính mạng detection xuấ… |
| `xiaofuqing13_nd_chineselpr` | xiaofuqing13/chinese-license-plate-recognition --- YOLOv5 + PlateNet, ho tro bien 2 tang | **01-citation-map.md**: tools & docs; **ocr**: 7.4 |
| `ultralytics_nd_issue2533` | ultralytics Issue #2533 --- train YOLOv8-pose voi 4 keypoint de lay 4 goc bien so | **ocr**: 4.3.1, 7.4 |
| `winter2897_2021_jetsonnano` | Real-time Auto License Plate Recognition with Jetson Nano | **dataset**: 2.1, 8.1, 9.2; **research**: 2.7.5, H. Mã nguồn mở về biển số Việt Nam |
| `trungdinh22_2022_lpr` | trungdinh22/License-Plate-Recognition --- nhan dang bien so Viet Nam bang YOLOv5 | **01-citation-map.md**: datasets; **dataset**: 2.1; **ocr**: 7.4, PA-5 — Kiểm tra tính thẳng hàng của …, pa-5 — kiểm tra tính thẳng hàng của …; **research**: 2.2.3, H. Mã nguồn mở về biển số Việt Nam |
| `trungdinh22_nd_helper` | function/helper.py --- logic phan biet bien 1 dong / 2 dong bang kiem tra thang hang (abs_tol=3) va ghep theo y_mean | **ocr**: 7.4, PA-5 — Kiểm tra tính thẳng hàng của …; **research**: H. Mã nguồn mở về biển số Việt Nam |
| `longphungtuan94_2022_alprsystem` | longphungtuan94/ALPR_System | **research**: H. Mã nguồn mở về biển số Việt Nam |
| `quangnhat185_2020_platedetect` | quangnhat185/Plate_detect_and_recognize | **01-citation-map.md**: tools & docs; **research**: 2.7.5, H. Mã nguồn mở về biển số Việt Nam |
| `mrzaizai2k_2023_yolov7cnn` | mrzaizai2k/License-Plate-Recognition-YOLOv7-and-CNN | **01-citation-map.md**: tools & docs; **ocr**: 7.4; **research**: 2.7.5, H. Mã nguồn mở về biển số Việt Nam |
| `mrzaizai2k_2025_vietnameselp` | mrzaizai2k/VIETNAMESE_LICENSE_PLATE | **01-citation-map.md**: tools & docs; **ocr**: 7.4; **research**: 2.3.1, H. Mã nguồn mở về biển số Việt Nam |
| `nndam_2024_plategenerator` | Vietnamese License Plate Generator | **dataset**: 5.3, 5.4, 7.3, 9.4; **research**: 2.7.4, H. Mã nguồn mở về biển số Việt Nam |
| `tungedng2710_2026_trafficanalysis` | AI-Traffic-Analysis | **research**: H. Mã nguồn mở về biển số Việt Nam |
| `lenguyengiabao_nd_lprecognition` | LeNguyenGiaBao/license_plates_recognition --- WPOD + PaddleOCR | **01-citation-map.md**: tools & docs; **ocr**: 4.3.2, 4.5, 7.4; **vn-plate**: 9.3, 12.5 |
| `viscom_nd_vietanpr` | VietANPR --- phần mềm nhận diện biển số xe máy & xe hơi | **research**: 2.7.6, I. Bối cảnh, giải pháp thương mại và… |
| `eparking_nd_nhandangbienso` | Nhận dạng biển số xe tự động trong bãi giữ xe thông minh | **research**: 2.7.6, I. Bối cảnh, giải pháp thương mại và… |
| `vetc_nd_thuphikhongdung` | Ô tô đi qua trạm thu phí không dừng sẽ quét biển hay quét mã thẻ | **research**: 2.7.6, I. Bối cảnh, giải pháp thương mại và… |

---

## Further reading — KHÔNG được trích dẫn ở báo cáo nào

Các entry dưới đây nằm trong `references.bib` nhưng **không** xuất hiện ở bất kỳ báo cáo nào (đối chiếu 
19/07/2026, cả theo URL lẫn theo nội dung). Chúng được gom vào nhóm riêng 
`% === Further reading (not cited) ===` ở cuối file `.bib` để **không lẫn** với nguồn đã thực sự được trích.

> ⚠️ **Trước khi dùng bất kỳ entry nào ở đây trong quyển luận văn:** phải đọc và kiểm chứng lại nguồn, 
> rồi chuyển entry lên đúng mục chủ đề tương ứng trong `.bib`. Không được `\cite{}` thẳng từ nhóm này.

| Khóa BibTeX | Nguồn | Ghi chú |
|---|---|---|
| `aldahoul_2025_vehiclepaligemma` | Multitasking vision language models for vehicle plate recognition with VehiclePaliGemma | Đọc thêm — chưa dùng ở Phase 1 |
| `ijca_2025_indianplate` | Real-Time Indian Number Plate Recognition with YOLOv11 and EasyOCR: A Vision-based Pipeline | Đọc thêm — chưa dùng ở Phase 1 |
| `arxiv_2025_yoloevolution` | Ultralytics YOLO Evolution: An Overview of YOLO26, YOLO11, YOLOv8 and YOLOv5 | Đọc thêm — chưa dùng ở Phase 1 |
| `paddlepaddle_2025_inferenceengine` | Inference Engine and Configuration --- PaddleOCR 3.x (chon engine paddle_static / onnxruntime) | Đọc thêm — chưa dùng ở Phase 1 |
| `deepwiki_2025_paddlecpu` | CPU Optimization --- PaddleOCR (enable_mkldnn, cpu_threads, mkldnn_cache_capacity, use_mp) | Đọc thêm — chưa dùng ở Phase 1 |
| `microsoft_2023_trocrreadme` | microsoft/unilm --- TrOCR README | Đọc thêm — chưa dùng ở Phase 1 |
| `winter2897_nd_detectionvoc` | License Plate Detection dataset --- VOC format (Google Drive) | Đọc thêm — chưa dùng ở Phase 1 |
| `winter2897_nd_detectionyolo` | License Plate Detection dataset --- YOLO format (Google Drive) | Đọc thêm — chưa dùng ở Phase 1 |
| `winter2897_nd_recognitionvoc` | License Plate Recognition (nhan ky tu) dataset --- VOC format (Google Drive) | Đọc thêm — chưa dùng ở Phase 1 |
| `winter2897_nd_recognitionyolo` | License Plate Recognition (nhan ky tu) dataset --- YOLO format (Google Drive) | Đọc thêm — chưa dùng ở Phase 1 |
| `vksndgialai_2023_biensodinhdanh` | Biển số định danh và những quy định mới từ Thông tư 24/2023/TT-BCA | Đọc thêm — chưa dùng ở Phase 1 |
| `ultralytics_2026_openvinolatency` | OpenVINO Inference Optimization for YOLO --- che do Latency vs Throughput | Đọc thêm — chưa dùng ở Phase 1 |
| `ultralytics_2024_openvinobenchmark` | OpenVINO --- Ultralytics YOLO Docs (ban luu bang benchmark Intel Core i7-13700H cho YOLOv8n/s/m/l/x) | Đọc thêm — chưa dùng ở Phase 1 |
| `ultralytics_2024_fasteryolov8` | 3x Faster YOLOv8 with OpenVINO | Đọc thêm — chưa dùng ở Phase 1 |
| `li_2021_quantizednlp` | Faster and smaller quantized NLP with Hugging Face and ONNX Runtime | Đọc thêm — chưa dùng ở Phase 1 |
| `nascimento_2024_lpsrlacd` | Enhancing License Plate Super-Resolution --- ma nguon chinh thuc lpsr-lacd | Đọc thêm — chưa dùng ở Phase 1 |
| `elcom_nd_cameraphatnguoi` | Tăng cường giám sát giao thông qua hệ thống camera phạt nguội | Đọc thêm — chưa dùng ở Phase 1 |
| `viettel_nd_myparking` | Bãi đỗ xe thông minh My Parking | Đọc thêm — chưa dùng ở Phase 1 |
| `vnpt_nd_iparking` | Hệ thống quản lý bãi đỗ xe IPARKING SYSTEM | Đọc thêm — chưa dùng ở Phase 1 |
| `nttuan8_nd_biensoxemay` | Bài toán phát hiện biển số xe máy Việt Nam | Đọc thêm — chưa dùng ở Phase 1 |
| `elsevier_2026_dlreview` | Deep learning algorithms for license plate recognition: A review | Báo cáo `research` ghi rõ bài này **không được trích dẫn** vì chưa xác minh được tác giả/volume/số trang |

---

## Bảo trì

Bảng này **sinh bằng cách đối chiếu URL** giữa `references.bib` và 6 báo cáo, không gõ tay. Khi thêm nguồn mới:

1. Thêm entry vào `docs/references.bib` (đúng mục chủ đề, có `urldate`).
2. Thêm URL nội tuyến vào báo cáo tương ứng.
3. Chạy lại đối chiếu và cập nhật bảng này.

Bất biến cần giữ: **mọi entry ở các mục chủ đề đều phải có ít nhất một chỗ trích**; entry không có chỗ trích 
phải nằm ở nhóm *Further reading*. Nếu một entry ở mục chủ đề mà cột "Trích ở đâu" trống thì hoặc URL trong 
báo cáo bị lệch dạng (phải thống nhất), hoặc entry đó thực sự mồ côi (phải chuyển xuống *Further reading*).
