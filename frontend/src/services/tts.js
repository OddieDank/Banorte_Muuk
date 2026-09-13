export async function describirUI(texto) {
    try {
        const respuesta = await fetch("http://localhost:8000/tts", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                text: texto,
            }),
        });

        if (!respuesta.ok) {
            console.error(
                "Error generando audio:",
                await respuesta.text()
            );
            return;
        }

        const audioBlob = await respuesta.blob();
        const audioUrl = URL.createObjectURL(audioBlob);

        const audio = new Audio(audioUrl);

        audio.onended = () => {
            URL.revokeObjectURL(audioUrl);
        };

        await audio.play();

    } catch (error) {
        console.error("Error conectando con TTS:", error);
    }
}