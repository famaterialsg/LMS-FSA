import google.generativeai as genai

def AIInsightModel(score,score_history):
    genai.configure(api_key="AIzaSyCqoUw4bZ9t6cFj7xzTgkNs_sSxcJD51Zg")
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    )

    chat_session = model.start_chat(
    history=[
    ]
    )
    if score_history[:-1]:
        response1 = chat_session.send_message(f"học sinh vừa đc số điểm {score}, và số điểm trước đó học sinh này làm được là:{score_history[:-1]}, những điểm số trên đều là của 1 môn, CHỈ XÉT VỀ NHỮNG ĐIỂM SỐ TRÊN, hãy cho nhận xét học sinh có điểm thấp hay cao, có tiến bộ hay thục lùi, có thể nhận xét thêm. Chỉ dựa vào những điểm học sinh đạt được, học sinh này có khả năng cao đậu môn này hay không (trên 5 là có thể đậu), bắt buộc nhận xét. Viết thành 1 đoạn ngắn")


        response2 = chat_session.send_message(f"""Từ nhận xét trước hãy xếp loại nhận xét là Bad, Try Harder, Improvement, Worsening, Good.
            Bad là điểm tệ, không có sự chêch lệch nhiều giữa các điểm, thường là dưới trung bình, có thể có ngoại lệ.                  
            Improvement là đang có nhiều điểm tệ đột nhiên có điểm cao và có sự chêch lệch nhiều so với các điểm trước theo hướng tích cực. 
            Worsening là đang có nhiều điểm cao đột nhiên có điểm thấp và có sự chêch lệch nhiều so với các điểm trước theo hướng tiêu cực.
            Try Harder không có sự chêch lệch nhiều giữa các điểm. Không tiến bộ, cũng không thụt lùi, thường dao động từ 5 đến 8
            Good là điểm tốt, thường là trên 8, không có sự chêch lệch nhiều giữa các điểm, có thể có ngoại lệ.
            Lưu ý: chỉ trả lời một trong 5:Bad, Try Harder, Improvement, Worsening, Good""")
        return response1.text, response2.text
    else:
        response1 = chat_session.send_message(f"học sinh vừa đc số điểm {score}. Chỉ xét về điểm số lần này, hãy cho nhận xét học sinh có điểm thấp hay cao, có thể nhận xét thêm. Viết thành 1 đoạn ngắn")
        response2 = chat_session.send_message(f"""Từ nhận xét trước, hãy xếp loại nhận xét là Bad, Try Harder, Good.
            Bad là điểm tệ, dưới 5     
            Try Harder là điểm từ 5 đến 8
            Good là điểm tốt, thường là trên 8
            Lưu ý: chỉ trả lời một trong 3:Bad, Try Harder, Good""")
        return response1.text, response2.text