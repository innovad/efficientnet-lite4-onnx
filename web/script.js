function checkFiles(files) {

    console.log(files[0]);

    const formData  = new FormData();
    for(const name in files) {
      formData.append(name, files[name]);
    }

    fetch('/analyze', { 
        method: 'POST',
        headers: {
        },
        body: formData 
    }).then(
        response => {
            console.log(response) 
            response.text().then(function (text) {
                alert(text)
              });
            
        }
    ).then(
        success => console.log(success) 
    ).catch(
        error => console.log(error) 
    );

}