# DeepScholar

## Giới thiệu

Đây là một hệ thống multi-agent được xây dựng để hỗ trợ nghiên cứu khoa học bằng cách tự động hóa việc thu thập, phân tích và tương tác với nội dung của các bài báo khoa học. Người dùng có thể cung cấp URL của một bài báo, và hệ thống sẽ:
1.  Tải xuống và trích xuất nội dung bài báo.
2.  Phân tích, tóm tắt bài báo chính.
3.  Xác định và có khả năng truy xuất thông tin từ các bài báo được trích dẫn.
4.  Cho phép người dùng trò chuyện và đặt câu hỏi về nội dung của các bài báo.

Dự án này sử dụng **LangChain** để xây dựng các agent riêng lẻ và **CrewAI** để tổ chức và điều phối sự hợp tác giữa chúng.

## Tính năng chính

*   **Thu thập tự động:** Tải bài báo từ URL được cung cấp (hỗ trợ PDF và trang web).
*   **Trích xuất tham khảo:** Tự động xác định và trích xuất danh sách tài liệu tham khảo từ bài báo chính.
*   **Phân tích chuyên sâu:** Tóm tắt nội dung, xác định các điểm chính, phương pháp luận, kết quả của bài báo.
*   **Nghiên cứu mở rộng:** Khả năng tìm kiếm và phân tích các bài báo được trích dẫn để làm rõ thông tin.
*   **Tương tác thông minh:** Giao diện trò chuyện cho phép người dùng đặt câu hỏi và khám phá sâu hơn về nội dung.
*   **Kiến trúc Multi-Agent:** Phân chia nhiệm vụ rõ ràng giữa các agent chuyên biệt (Retriever, Analyzer, Researcher, Conversationalist).

## Luồng hoạt động của hệ thống

1.  **Người dùng cung cấp URL:** Thông qua API endpoint.
2.  **CrewAI Kickoff:** `PaperAnalysisCrew` được kích hoạt.
    *   **Retriever Agent:**
        *   **Task:** Tải bài báo từ URL.
        *   **Task:** Trích xuất danh sách tài liệu tham khảo.
    *   **Analyzer Agent:**
        *   **Task:** Phân tích và tóm tắt bài báo chính (dựa trên output của Retriever Agent).
    *   *(Kết quả phân tích ban đầu có thể được trả về cho người dùng ở bước này)*
3.  **Tương tác qua Chat:**
    *   **Conversation Agent:**
        *   **Task:** Nhận câu hỏi từ người dùng.
        *   Sử dụng kiến thức đã phân tích (từ Analyzer Agent) để trả lời.
        *   Nếu cần làm rõ thông tin hoặc người dùng hỏi về một tài liệu tham khảo, Conversation Agent có thể ủy thác (delegate) nhiệm vụ cho **Research Agent**.
    *   **Research Agent (nếu được kích hoạt):**
        *   **Task:** Tìm kiếm, tải và phân tích bài báo tham khảo cụ thể.
        *   Cung cấp thông tin bổ sung cho Conversation Agent.
4.  **Coordinator (CrewAI):** Điều phối luồng công việc, truyền dữ liệu giữa các agent và task, quản lý ngữ cảnh chung.

## Roadmap tương lai (Ví dụ)

*   [ ] Hỗ trợ thêm nhiều định dạng tài liệu.
*   [ ] Cải thiện độ chính xác của việc trích xuất tham khảo.
*   [ ] Tích hợp khả năng so sánh giữa nhiều bài báo.
*   [ ] Xây dựng giao diện người dùng (Frontend).
*   [ ] Triển khai hệ thống lên cloud.
*   [ ] Tối ưu hóa tốc độ và chi phí sử dụng LLM.