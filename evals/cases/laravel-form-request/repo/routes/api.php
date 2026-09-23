<?php

use App\Http\Controllers\InvoiceController;
use Illuminate\Support\Facades\Route;

Route::post('/invoices', [InvoiceController::class, 'store']);
