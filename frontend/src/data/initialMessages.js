export const initialMessages = [
  {
    id: 1,
    role: 'ai',
    text: 'Chào bạn! Tôi là Trợ lý AI Pháp lý của bạn. Làm thế nào tôi có thể hỗ trợ bạn hôm nay?',
    chips: ['Tạo Hợp Đồng', 'Kiểm Tra Tuân Thủ', 'Tìm Kiếm Tiền Lệ'],
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
  },
  {
    id: 2,
    role: 'user',
    text: 'Tôi cần tư vấn về việc thành lập công ty cổ phần. Thủ tục cần những gì?',
    timestamp: new Date(Date.now() - 4 * 60 * 1000),
  },
  {
    id: 3,
    role: 'ai',
    text: 'Để thành lập công ty cổ phần tại Việt Nam, bạn cần thực hiện các bước sau:\n\n1. **Chuẩn bị hồ sơ** bao gồm: Giấy đề nghị đăng ký doanh nghiệp, Điều lệ công ty, Danh sách cổ đông sáng lập, Bản sao CCCD/Hộ chiếu của cổ đông.\n\n2. **Nộp hồ sơ** tại Sở Kế hoạch và Đầu tư.\n\n3. **Nhận Giấy chứng nhận** đăng ký doanh nghiệp.\n\n4. **Khắc dấu** và công bố thông tin doanh nghiệp.',
    chips: ['Mẫu Hồ Sơ Thành Lập', 'Tư Vấn Thuế', 'Yêu Cầu Hỗ Trợ Trực Tiếp'],
    timestamp: new Date(Date.now() - 3 * 60 * 1000),
  },
  {
    id: 4,
    role: 'user',
    text: "Tuyệt vời! Tôi có một tài liệu cần xem xét lại. Nó liên quan đến một hợp đồng mua bán bất động sản. Tôi có thể đính kèm nó không?",
    timestamp: new Date(Date.now() - 2 * 60 * 1000),
  },
  {
    id: 5,
    role: 'ai',
    text: 'Vâng, tất nhiên rồi! Bạn có thể sử dụng biểu tượng kẹp giấy bên cạnh ô nhập tin nhắn để đính kèm tài liệu. Sau khi bạn đính kèm, tôi sẽ tiến hành phân tích hợp đồng mua bán bất động sản và cung cấp cho bạn những điểm cần lưu ý.',
    chips: ['Phân Tích Hợp Đồng', 'Tóm Tắt Điểm Chính'],
    timestamp: new Date(Date.now() - 1 * 60 * 1000),
  },
];

export const quickActions = [
  {
    id: 'draft',
    icon: 'FileText',
    label: 'Soạn thảo văn bản pháp lý',
    description: 'Hợp đồng, thỏa thuận, công văn...',
  },
  {
    id: 'verify',
    icon: 'Scale',
    label: 'Kiểm tra tính hợp pháp của tài liệu',
    description: 'Xác minh giá trị pháp lý của văn bản',
  },
  {
    id: 'report',
    icon: 'ShieldAlert',
    label: 'Báo cáo vi phạm hoặc rủi ro',
    description: 'Phân tích và báo cáo rủi ro pháp lý',
  },
  {
    id: 'ip',
    icon: 'Lightbulb',
    label: 'Tư vấn về quyền sở hữu trí tuệ',
    description: 'Bằng sáng chế, nhãn hiệu và bản quyền',
  },
  {
    id: 'search',
    icon: 'Search',
    label: 'Tìm kiếm thông tin pháp luật',
    description: 'Luật, nghị định và thông tư',
  },
  {
    id: 'consult',
    icon: 'Sparkles',
    label: 'Gợi ý pháp lý chuyên sâu',
    description: 'Tư vấn pháp lý nâng cao dựa trên AI',
  },
];
