<?php
    session_start();

    $testMode = true;
    $sessionID = uniqid();
    $orgID = $testMode ? '1snn5n9w' : 'k8vif92e';
    $mechantID = 'visanetgt_qpay';

?>
<html>
    <title>QPayPro - Fingerprint Example</title>
    <head>

    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

<body>
    <!-- DEVICE FINGERPRINT CODE -->
    <script src="https://h.online-metrix.net/fp/tags.js?org_id=<?php echo $orgID ?>&amp;session_id=<?php echo $mechantID?><?php echo $sessionID ?>" type="application/javascript"></script>

    <noscript>
    <iframe style="width: 100px; height: 100px; border: 0; position: absolute; top: -5000px;"
    src="https://h.online-metrix.net/fp/tags?org_id=<?php echo $orgID ?>&amp;session_id=<?php echo $mechantID?><?php echo $sessionID ?>" >
    </iframe>
    </noscript>
    <!-- END DEVICE FINGERPRINT CODE -->
    </head>

    <?php
        $array = array(
            "x_login" => "visanetgt_qpay",
            "x_private_key" => "88888888888",
            "x_api_secret" => "99999999999",
            "x_product_id" => 6,
            "x_audit_number" => rand(1,999999),
            "x_fp_sequence" => 1988679099,
            "x_fp_timestamp" => time(),
            "x_invoice_num" => rand(1,999999),
            "x_currency_code" => "GTQ",
            "x_amount" => 1.00,
            "x_line_item" => "T-shirt Live Dreams<|>w01<|><|>1<|>1000.00<|>N",
            "x_freight" => 0.00,
            "x_email" => "test@email.com",
            "cc_number" => "4111111111111111",
            "cc_exp" => "01/21",
            "cc_cvv2" => "4567",
            "cc_name" => "john doe",
            "cc_type" => "visa",
            "x_first_name" =>  "john",
            "x_last_name" =>  "doe",
            "x_company" => "Company",
            "x_address" => "711-2880 Nulla",
            "x_city" => "Guatemala",
            "x_state" => "Guatemala",
            "x_country" => "Guatemala",
            "x_zip" => "01056",
            "x_relay_response" => "none",
            "x_relay_url" => "none",
            "x_type" => "AUTH_ONLY",
            "x_method" => "CC",
            "http_origin" => "http://local.test.com",
            "visaencuotas" => 0,
            "device_fingerprint_id" => $sessionID
        );
    ?>

    <div class="row">
    <div class="col-md-6">
        <form method="post" action="https://sandbox.qpaypro.com/payment/api_v1" class="form-inline">

            <table class="table">
                <th></th>
                <tbody>
                    <?php foreach($array as $i => $v){ ?>
                    <tr>
                        <td><?php echo $i ?></td>
                        <td><input type="text" class="form-control" name="<?php echo $i?>" value="<?php echo $v?>"></td>
                    </tr>
                    <?php } ?>
                </tbody>
            </table>

            <input type="submit" value="Submit" class="btn btn-default">
        </form>
    </div>
    </div>

    </body>
</html>